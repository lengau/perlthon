use std::ffi::{CStr, CString, c_char, c_double, c_int, c_longlong};
use std::ptr;
use std::sync::Mutex;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

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

    fn perlthon_sv_decref(interp: *mut PerlInterpreterC, sv: *mut SV);
    fn perlthon_free_error(error: *mut c_char);
}

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
        0 => Ok(py.None()), // undef
        1 => {
            // integer
            let val = unsafe { perlthon_sv_iv(interp, sv) };
            Ok(val.into_pyobject(py)?.into_any().unbind())
        }
        2 => {
            // float
            let val = unsafe { perlthon_sv_nv(interp, sv) };
            Ok(val.into_pyobject(py)?.into_any().unbind())
        }
        3 => {
            // string
            let mut len: usize = 0;
            let ptr = unsafe { perlthon_sv_pv(interp, sv, &mut len) };
            let bytes = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
            let s = String::from_utf8_lossy(bytes);
            Ok(s.as_ref().into_pyobject(py)?.into_any().unbind())
        }
        4 => {
            // arrayref
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
            // hashref
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
            // Other ref types: convert to string representation
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
    // Fallback: stringify
    let s = obj.str()?.to_string();
    let c = CString::new(s.as_bytes())
        .map_err(|_| PyRuntimeError::new_err("String contains null byte"))?;
    Ok(unsafe { perlthon_new_sv_pv(interp, c.as_ptr(), s.len()) })
}

/// A Python module implemented in Rust.
#[pymodule]
mod _core {
    use super::*;

    #[pyfunction]
    fn hello_from_bin() -> String {
        "Hello from perlthon!".to_string()
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
            Ok(PerlInterpreter {
                inner: Mutex::new(interp),
            })
        }

        fn use_module(&self, module_name: &str) -> PyResult<()> {
            let interp = self.inner.lock().unwrap();
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
            let c_name = CString::new(func_name)
                .map_err(|_| PyRuntimeError::new_err("Function name contains null byte"))?;

            let mut sv_args: Vec<*mut SV> = Vec::with_capacity(args.len());
            for arg in &args {
                sv_args.push(unsafe { py_to_sv(py, *interp, arg) }?);
            }

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
            let c_module = CString::new(module)
                .map_err(|_| PyRuntimeError::new_err("Module name contains null byte"))?;
            let c_method = CString::new(method)
                .map_err(|_| PyRuntimeError::new_err("Method name contains null byte"))?;

            let mut sv_args: Vec<*mut SV> = Vec::with_capacity(args.len());
            for arg in &args {
                sv_args.push(unsafe { py_to_sv(py, *interp, arg) }?);
            }

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
            unsafe { check_error(error) }?;
            let result = unsafe { sv_to_py(py, *interp, sv) };
            if !sv.is_null() {
                unsafe { perlthon_sv_decref(*interp, sv) };
            }
            result
        }
    }

    impl Drop for PerlInterpreter {
        fn drop(&mut self) {
            let interp = self.inner.lock().unwrap();
            if !(*interp).is_null() {
                unsafe { perlthon_destroy(*interp) };
            }
        }
    }
}
