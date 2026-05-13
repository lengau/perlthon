use std::collections::HashMap;
use std::ffi::{CStr, CString, c_char, c_double, c_int, c_longlong};
use std::ptr;
use std::sync::{LazyLock, Mutex};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

// Opaque types for Perl's internal structures
#[repr(C)]
struct PerlInterpreterC {
    _private: [u8; 0],
}
#[repr(C)]
struct SV {
    _private: [u8; 0],
}

// FFI declarations for our C glue
unsafe extern "C" {
    fn perlthon_alloc() -> *mut PerlInterpreterC;
    fn perlthon_init(interp: *mut PerlInterpreterC) -> c_int;
    fn perlthon_destroy(interp: *mut PerlInterpreterC);

    fn perlthon_eval(
        interp: *mut PerlInterpreterC,
        code: *const c_char,
        error: *mut *mut c_char,
    ) -> *mut SV;

    fn perlthon_use_module(
        interp: *mut PerlInterpreterC,
        module_name: *const c_char,
        error: *mut *mut c_char,
    ) -> c_int;

    fn perlthon_call_function(
        interp: *mut PerlInterpreterC,
        func_name: *const c_char,
        argc: c_int,
        argv: *mut *mut SV,
        error: *mut *mut c_char,
    ) -> *mut SV;

    fn perlthon_call_method(
        interp: *mut PerlInterpreterC,
        module: *const c_char,
        method: *const c_char,
        argc: c_int,
        argv: *mut *mut SV,
        error: *mut *mut c_char,
    ) -> *mut SV;

    fn perlthon_install_callback(
        interp: *mut PerlInterpreterC,
        name: *const c_char,
        error: *mut *mut c_char,
    ) -> c_int;

    fn perlthon_sv_type(interp: *mut PerlInterpreterC, sv: *mut SV) -> c_int;
    fn perlthon_sv_iv(interp: *mut PerlInterpreterC, sv: *mut SV) -> c_longlong;
    fn perlthon_sv_nv(interp: *mut PerlInterpreterC, sv: *mut SV) -> c_double;
    fn perlthon_sv_pv(interp: *mut PerlInterpreterC, sv: *mut SV, len: *mut usize)
    -> *const c_char;

    fn perlthon_av_len(interp: *mut PerlInterpreterC, sv: *mut SV) -> c_int;
    fn perlthon_av_fetch(interp: *mut PerlInterpreterC, sv: *mut SV, index: c_int) -> *mut SV;

    fn perlthon_hv_iterinit(interp: *mut PerlInterpreterC, sv: *mut SV) -> c_int;
    fn perlthon_hv_iternext(
        interp: *mut PerlInterpreterC,
        sv: *mut SV,
        key: *mut *const c_char,
        klen: *mut usize,
        val: *mut *mut SV,
    ) -> c_int;

    fn perlthon_new_sv_iv(interp: *mut PerlInterpreterC, val: c_longlong) -> *mut SV;
    fn perlthon_new_sv_nv(interp: *mut PerlInterpreterC, val: c_double) -> *mut SV;
    fn perlthon_new_sv_pv(interp: *mut PerlInterpreterC, s: *const c_char, len: usize) -> *mut SV;
    fn perlthon_new_sv_bool(interp: *mut PerlInterpreterC, val: c_int) -> *mut SV;
    fn perlthon_new_sv_undef(interp: *mut PerlInterpreterC) -> *mut SV;
    fn perlthon_new_av(interp: *mut PerlInterpreterC) -> *mut SV;
    fn perlthon_av_push(interp: *mut PerlInterpreterC, av: *mut SV, value: *mut SV);
    fn perlthon_new_hv(interp: *mut PerlInterpreterC) -> *mut SV;
    fn perlthon_hv_store(
        interp: *mut PerlInterpreterC,
        hv: *mut SV,
        key: *const c_char,
        klen: usize,
        value: *mut SV,
    ) -> c_int;

    fn perlthon_sv_decref(interp: *mut PerlInterpreterC, sv: *mut SV);
    fn perlthon_free_error(error: *mut c_char);
    fn strdup(s: *const c_char) -> *mut c_char;
}

type CallbackKey = (usize, String);
type CallbackRegistry = HashMap<CallbackKey, Py<PyAny>>;

static CALLBACK_REGISTRY: LazyLock<Mutex<CallbackRegistry>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));
static CURRENT_INTERPRETER: LazyLock<Mutex<usize>> = LazyLock::new(|| Mutex::new(0));

/// Check the error pointer and return a PyErr if set.
unsafe fn check_error(error: *mut c_char) -> PyResult<()> {
    if error.is_null() {
        Ok(())
    } else {
        let msg = unsafe { CStr::from_ptr(error) }
            .to_string_lossy()
            .to_string();
        unsafe { perlthon_free_error(error) };
        Err(PyRuntimeError::new_err(msg))
    }
}

/// Convert a Perl SV to a Python object. Recursively handles array/hash refs.
unsafe fn sv_to_py(
    py: Python<'_>,
    interp: *mut PerlInterpreterC,
    sv: *mut SV,
) -> PyResult<Py<PyAny>> {
    if sv.is_null() {
        return Ok(py.None());
    }

    let svtype = unsafe { perlthon_sv_type(interp, sv) };
    match svtype {
        0 => Ok(py.None()),
        1 => {
            let val = unsafe { perlthon_sv_iv(interp, sv) };
            Ok(val.into_pyobject(py)?.into_any().unbind())
        }
        2 => {
            let val = unsafe { perlthon_sv_nv(interp, sv) };
            Ok(val.into_pyobject(py)?.into_any().unbind())
        }
        3 => {
            let mut len: usize = 0;
            let ptr = unsafe { perlthon_sv_pv(interp, sv, &mut len) };
            let bytes = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
            let s = String::from_utf8_lossy(bytes);
            Ok(s.as_ref().into_pyobject(py)?.into_any().unbind())
        }
        4 => {
            let count = unsafe { perlthon_av_len(interp, sv) };
            let list = PyList::empty(py);
            for i in 0..count {
                let elem = unsafe { perlthon_av_fetch(interp, sv, i) };
                let py_elem = unsafe { sv_to_py(py, interp, elem) }?;
                list.append(py_elem)?;
                if !elem.is_null() {
                    unsafe { perlthon_sv_decref(interp, elem) };
                }
            }
            Ok(list.into_any().unbind())
        }
        5 => {
            let dict = PyDict::new(py);
            unsafe { perlthon_hv_iterinit(interp, sv) };
            loop {
                let mut key: *const c_char = ptr::null();
                let mut klen: usize = 0;
                let mut val: *mut SV = ptr::null_mut();
                let has_next =
                    unsafe { perlthon_hv_iternext(interp, sv, &mut key, &mut klen, &mut val) };
                if has_next == 0 {
                    break;
                }
                let key_bytes = unsafe { std::slice::from_raw_parts(key as *const u8, klen) };
                let key_str = String::from_utf8_lossy(key_bytes);
                let py_val = unsafe { sv_to_py(py, interp, val) }?;
                dict.set_item(key_str.as_ref(), py_val)?;
                if !val.is_null() {
                    unsafe { perlthon_sv_decref(interp, val) };
                }
            }
            Ok(dict.into_any().unbind())
        }
        _ => {
            let mut len: usize = 0;
            let ptr = unsafe { perlthon_sv_pv(interp, sv, &mut len) };
            let bytes = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
            let s = String::from_utf8_lossy(bytes);
            Ok(s.as_ref().into_pyobject(py)?.into_any().unbind())
        }
    }
}

/// Convert a Python object to a Perl SV.
unsafe fn py_to_sv(
    _py: Python<'_>,
    interp: *mut PerlInterpreterC,
    obj: &Bound<'_, pyo3::PyAny>,
) -> PyResult<*mut SV> {
    if obj.is_none() {
        return Ok(unsafe { perlthon_new_sv_undef(interp) });
    }
    if let Ok(val) = obj.extract::<bool>() {
        return Ok(unsafe { perlthon_new_sv_bool(interp, if val { 1 } else { 0 }) });
    }
    if let Ok(val) = obj.extract::<i64>() {
        return Ok(unsafe { perlthon_new_sv_iv(interp, val as c_longlong) });
    }
    if let Ok(val) = obj.extract::<f64>() {
        return Ok(unsafe { perlthon_new_sv_nv(interp, val) });
    }
    if let Ok(val) = obj.extract::<String>() {
        let c = CString::new(val.as_bytes())
            .map_err(|_| PyRuntimeError::new_err("String contains null byte"))?;
        return Ok(unsafe { perlthon_new_sv_pv(interp, c.as_ptr(), val.len()) });
    }
    if let Ok(list) = obj.cast::<PyList>() {
        let av = unsafe { perlthon_new_av(interp) };
        for item in list.iter() {
            let value = match unsafe { py_to_sv(_py, interp, &item) } {
                Ok(value) => value,
                Err(err) => {
                    unsafe { decref_sv(interp, av) };
                    return Err(err);
                }
            };
            unsafe { perlthon_av_push(interp, av, value) };
        }
        return Ok(av);
    }
    if let Ok(tuple) = obj.cast::<PyTuple>() {
        let av = unsafe { perlthon_new_av(interp) };
        for item in tuple.iter() {
            let value = match unsafe { py_to_sv(_py, interp, &item) } {
                Ok(value) => value,
                Err(err) => {
                    unsafe { decref_sv(interp, av) };
                    return Err(err);
                }
            };
            unsafe { perlthon_av_push(interp, av, value) };
        }
        return Ok(av);
    }
    if let Ok(dict) = obj.cast::<PyDict>() {
        let hv = unsafe { perlthon_new_hv(interp) };
        for (key, value) in dict.iter() {
            let key = match key.extract::<String>() {
                Ok(key) => key,
                Err(err) => {
                    unsafe { decref_sv(interp, hv) };
                    return Err(err);
                }
            };
            let c_key = match CString::new(key.as_bytes()) {
                Ok(c_key) => c_key,
                Err(_) => {
                    unsafe { decref_sv(interp, hv) };
                    return Err(PyRuntimeError::new_err("Dict key contains null byte"));
                }
            };
            let sv_value = match unsafe { py_to_sv(_py, interp, &value) } {
                Ok(sv_value) => sv_value,
                Err(err) => {
                    unsafe { decref_sv(interp, hv) };
                    return Err(err);
                }
            };
            let stored =
                unsafe { perlthon_hv_store(interp, hv, c_key.as_ptr(), key.len(), sv_value) };
            if stored == 0 {
                unsafe {
                    decref_sv(interp, sv_value);
                    decref_sv(interp, hv);
                };
                return Err(PyRuntimeError::new_err(
                    "Failed to store value in Perl hash",
                ));
            }
        }
        return Ok(hv);
    }

    let s = obj.str()?.to_string();
    let c = CString::new(s.as_bytes())
        .map_err(|_| PyRuntimeError::new_err("String contains null byte"))?;
    Ok(unsafe { perlthon_new_sv_pv(interp, c.as_ptr(), s.len()) })
}

fn set_current_interpreter(interp: *mut PerlInterpreterC) {
    *CURRENT_INTERPRETER.lock().unwrap() = interp as usize;
}

fn current_interpreter() -> *mut PerlInterpreterC {
    *CURRENT_INTERPRETER.lock().unwrap() as *mut PerlInterpreterC
}

unsafe fn decref_sv(interp: *mut PerlInterpreterC, sv: *mut SV) {
    if !sv.is_null() {
        unsafe { perlthon_sv_decref(interp, sv) };
    }
}

unsafe fn free_sv_args(interp: *mut PerlInterpreterC, args: &mut Vec<*mut SV>) {
    for sv in args.drain(..) {
        unsafe { decref_sv(interp, sv) };
    }
}

fn args_to_sv(
    py: Python<'_>,
    interp: *mut PerlInterpreterC,
    args: &[Bound<'_, pyo3::PyAny>],
) -> PyResult<Vec<*mut SV>> {
    let mut sv_args = Vec::with_capacity(args.len());
    for arg in args {
        match unsafe { py_to_sv(py, interp, arg) } {
            Ok(sv) => sv_args.push(sv),
            Err(err) => {
                unsafe { free_sv_args(interp, &mut sv_args) };
                return Err(err);
            }
        }
    }
    Ok(sv_args)
}

fn register_callback_impl(
    interp: *mut PerlInterpreterC,
    name: &str,
    callable: Py<PyAny>,
) -> PyResult<()> {
    let c_name = CString::new(name)
        .map_err(|_| PyRuntimeError::new_err("Callback name contains null byte"))?;

    let registry_key = (interp as usize, name.to_owned());
    let previous = {
        let mut registry = CALLBACK_REGISTRY.lock().unwrap();
        registry.insert(registry_key.clone(), callable)
    };

    let mut error: *mut c_char = ptr::null_mut();
    let rc = unsafe { perlthon_install_callback(interp, c_name.as_ptr(), &mut error) };
    if rc != 0 {
        let mut registry = CALLBACK_REGISTRY.lock().unwrap();
        if let Some(previous) = previous {
            registry.insert(registry_key, previous);
        } else {
            registry.remove(&registry_key);
        }
        unsafe { check_error(error) }
    } else {
        Ok(())
    }
}

#[unsafe(no_mangle)]
unsafe extern "C" fn perlthon_dispatch_callback(
    interp: *mut PerlInterpreterC,
    name: *const c_char,
    argc: c_int,
    argv: *mut *mut SV,
    error: *mut *mut c_char,
) -> *mut SV {
    if !error.is_null() {
        unsafe { *error = ptr::null_mut() };
    }

    let result = (|| -> PyResult<*mut SV> {
        let name = unsafe { CStr::from_ptr(name) }
            .to_str()
            .map_err(|_| PyRuntimeError::new_err("Callback name is not valid UTF-8"))?
            .to_owned();

        Python::attach(|py| {
            let callback = {
                let registry = CALLBACK_REGISTRY.lock().unwrap();
                registry
                    .get(&(interp as usize, name.clone()))
                    .map(|cb| cb.clone_ref(py))
                    .ok_or_else(|| {
                        PyRuntimeError::new_err(format!("No Python callback registered for {name}"))
                    })?
            };

            let py_args = if argc <= 0 || argv.is_null() {
                Vec::new()
            } else {
                let values = unsafe { std::slice::from_raw_parts(argv, argc as usize) };
                let mut converted = Vec::with_capacity(values.len());
                for value in values {
                    converted.push(unsafe { sv_to_py(py, interp, *value) }?);
                }
                converted
            };

            let tuple = PyTuple::new(py, py_args)?;
            let result = callback.call1(py, tuple)?;
            unsafe { py_to_sv(py, interp, result.bind(py)) }
        })
    })();

    match result {
        Ok(sv) => sv,
        Err(err) => {
            if !error.is_null() {
                let message = err.to_string();
                if let Ok(message) = CString::new(message) {
                    unsafe { *error = strdup(message.as_ptr()) };
                }
            }
            ptr::null_mut()
        }
    }
}

/// A Python module implemented in Rust.
#[pymodule]
mod _core {
    use super::*;

    #[pyfunction]
    fn hello_from_bin() -> String {
        "Hello from perlthon!".to_string()
    }

    #[pyfunction]
    fn register_callback(name: &str, callable: Py<PyAny>) -> PyResult<()> {
        let interp = current_interpreter();
        if interp.is_null() {
            return Err(PyRuntimeError::new_err(
                "No active Perl interpreter available for callback registration",
            ));
        }
        register_callback_impl(interp, name, callable)
    }

    #[pyclass]
    struct PerlInterpreter {
        inner: Mutex<*mut PerlInterpreterC>,
    }

    // Safety: The Mutex ensures only one thread accesses the interpreter at a time.
    // Perl is not thread-safe, but we serialize access.
    unsafe impl Send for PerlInterpreter {}
    unsafe impl Sync for PerlInterpreter {}

    #[pymethods]
    impl PerlInterpreter {
        #[new]
        fn new() -> PyResult<Self> {
            let interp = unsafe { perlthon_alloc() };
            if interp.is_null() {
                return Err(PyRuntimeError::new_err(
                    "Failed to allocate Perl interpreter",
                ));
            }
            let rc = unsafe { perlthon_init(interp) };
            if rc != 0 {
                unsafe { perlthon_destroy(interp) };
                return Err(PyRuntimeError::new_err(
                    "Failed to initialize Perl interpreter",
                ));
            }
            set_current_interpreter(interp);
            Ok(PerlInterpreter {
                inner: Mutex::new(interp),
            })
        }

        fn use_module(&self, module_name: &str) -> PyResult<()> {
            let interp = self.inner.lock().unwrap();
            set_current_interpreter(*interp);
            let c_name = CString::new(module_name)
                .map_err(|_| PyRuntimeError::new_err("Module name contains null byte"))?;
            let mut error: *mut c_char = ptr::null_mut();
            let rc = unsafe { perlthon_use_module(*interp, c_name.as_ptr(), &mut error) };
            if rc != 0 {
                unsafe { check_error(error) }
            } else {
                Ok(())
            }
        }

        fn eval(&self, py: Python<'_>, code: &str) -> PyResult<Py<PyAny>> {
            let interp = self.inner.lock().unwrap();
            set_current_interpreter(*interp);
            let c_code = CString::new(code)
                .map_err(|_| PyRuntimeError::new_err("Code contains null byte"))?;
            let mut error: *mut c_char = ptr::null_mut();
            let sv = unsafe { perlthon_eval(*interp, c_code.as_ptr(), &mut error) };
            unsafe { check_error(error) }?;
            let result = unsafe { sv_to_py(py, *interp, sv) };
            if !sv.is_null() {
                unsafe { perlthon_sv_decref(*interp, sv) };
            }
            result
        }

        fn call_function(
            &self,
            py: Python<'_>,
            func_name: &str,
            args: Vec<Bound<'_, pyo3::PyAny>>,
        ) -> PyResult<Py<PyAny>> {
            let interp = self.inner.lock().unwrap();
            set_current_interpreter(*interp);
            let c_name = CString::new(func_name)
                .map_err(|_| PyRuntimeError::new_err("Function name contains null byte"))?;
            let mut sv_args = args_to_sv(py, *interp, &args)?;

            let mut error: *mut c_char = ptr::null_mut();
            let sv = unsafe {
                perlthon_call_function(
                    *interp,
                    c_name.as_ptr(),
                    sv_args.len() as c_int,
                    sv_args.as_mut_ptr(),
                    &mut error,
                )
            };
            unsafe { free_sv_args(*interp, &mut sv_args) };
            unsafe { check_error(error) }?;
            let result = unsafe { sv_to_py(py, *interp, sv) };
            if !sv.is_null() {
                unsafe { perlthon_sv_decref(*interp, sv) };
            }
            result
        }

        fn call_method(
            &self,
            py: Python<'_>,
            module: &str,
            method: &str,
            args: Vec<Bound<'_, pyo3::PyAny>>,
        ) -> PyResult<Py<PyAny>> {
            let interp = self.inner.lock().unwrap();
            set_current_interpreter(*interp);
            let c_module = CString::new(module)
                .map_err(|_| PyRuntimeError::new_err("Module name contains null byte"))?;
            let c_method = CString::new(method)
                .map_err(|_| PyRuntimeError::new_err("Method name contains null byte"))?;
            let mut sv_args = args_to_sv(py, *interp, &args)?;

            let mut error: *mut c_char = ptr::null_mut();
            let sv = unsafe {
                perlthon_call_method(
                    *interp,
                    c_module.as_ptr(),
                    c_method.as_ptr(),
                    sv_args.len() as c_int,
                    sv_args.as_mut_ptr(),
                    &mut error,
                )
            };
            unsafe { free_sv_args(*interp, &mut sv_args) };
            unsafe { check_error(error) }?;
            let result = unsafe { sv_to_py(py, *interp, sv) };
            if !sv.is_null() {
                unsafe { perlthon_sv_decref(*interp, sv) };
            }
            result
        }

        fn register_callback(&self, name: &str, callable: Py<PyAny>) -> PyResult<()> {
            let interp = self.inner.lock().unwrap();
            set_current_interpreter(*interp);
            register_callback_impl(*interp, name, callable)
        }
    }

    impl Drop for PerlInterpreter {
        fn drop(&mut self) {
            let interp = self.inner.lock().unwrap();
            if !(*interp).is_null() {
                let interp_id = *interp as usize;
                let mut registry = CALLBACK_REGISTRY.lock().unwrap();
                registry.retain(|(registered_interp, _), _| *registered_interp != interp_id);
                drop(registry);

                let mut current = CURRENT_INTERPRETER.lock().unwrap();
                if *current == interp_id {
                    *current = 0;
                }
                unsafe { perlthon_destroy(*interp) };
            }
        }
    }
}
