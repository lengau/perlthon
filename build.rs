use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

fn c_string_define(value: &str) -> String {
    format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
}

fn perl_library_search_paths() -> String {
    let perl_lib_search = Command::new("perl")
        .args([
            "-MConfig",
            "-e",
            r#"print "$Config{archlib}/CORE\n$Config{libpth}""#,
        ])
        .output()
        .expect("Failed to get Perl lib paths");

    String::from_utf8(perl_lib_search.stdout).expect("Perl lib paths were not valid UTF-8")
}

fn find_libperl(search_paths: &str) -> Option<PathBuf> {
    for search_dir in search_paths.split_whitespace() {
        let unversioned = Path::new(search_dir).join("libperl.so");
        if unversioned.exists() {
            return Some(fs::canonicalize(&unversioned).unwrap_or(unversioned));
        }
    }

    for search_dir in search_paths.split_whitespace() {
        for entry in fs::read_dir(search_dir).into_iter().flatten().flatten() {
            let path = entry.path();
            let Some(name) = path.file_name().and_then(|name| name.to_str()) else {
                continue;
            };
            if name.starts_with("libperl.so.") && !name.ends_with(".1") {
                return Some(path);
            }
        }
    }

    None
}

fn main() {
    let ccopts = Command::new("perl")
        .args(["-MExtUtils::Embed", "-e", "ccopts"])
        .output()
        .expect("Failed to run perl for ccopts — is Perl installed?");
    let ccopts = String::from_utf8(ccopts.stdout).unwrap();

    let ldopts = Command::new("perl")
        .args(["-MExtUtils::Embed", "-e", "ldopts"])
        .output()
        .expect("Failed to run perl for ldopts");
    let ldopts = String::from_utf8(ldopts.stdout).unwrap();

    let search_paths = perl_library_search_paths();
    let resolved_libperl = find_libperl(&search_paths);

    let mut cc = cc::Build::new();
    cc.file("csrc/perl_glue.c");

    for flag in ccopts.split_whitespace() {
        if let Some(path) = flag.strip_prefix("-I") {
            cc.include(path);
        } else if let Some(define) = flag.strip_prefix("-D") {
            if let Some((key, value)) = define.split_once('=') {
                cc.define(key, Some(value));
            } else {
                cc.define(define, None);
            }
        }
    }

    if let Some(path) = &resolved_libperl {
        let path_string = path.display().to_string();
        let path_define = c_string_define(&path_string);
        cc.define("PERLTHON_LIBPERL_PATH", Some(path_define.as_str()));

        if let Some(soname) = path.file_name().and_then(|name| name.to_str()) {
            let soname_define = c_string_define(soname);
            cc.define("PERLTHON_LIBPERL_SONAME", Some(soname_define.as_str()));
        }
    }

    cc.warnings(false);
    cc.compile("perl_glue");

    for flag in ldopts.split_whitespace() {
        if flag == "-Wl,-E" {
            println!("cargo:rustc-link-arg=-Wl,-E");
        }
    }
    println!("cargo:rustc-link-arg=-Wl,--export-dynamic");

    let mut found_perl_lib = false;
    for flag in ldopts.split_whitespace() {
        if let Some(path) = flag.strip_prefix("-L") {
            println!("cargo:rustc-link-search=native={path}");
        } else if let Some(lib) = flag.strip_prefix("-l") {
            if lib == "perl" {
                found_perl_lib = true;
            } else {
                println!("cargo:rustc-link-lib={lib}");
            }
        }
    }

    if found_perl_lib {
        let Some(resolved_libperl) = resolved_libperl else {
            panic!(
                "Could not find libperl.so — install libperl-dev or ensure Perl development libraries are available"
            );
        };

        let parent = resolved_libperl
            .parent()
            .expect("Resolved libperl path did not have a parent directory");
        let unversioned = parent.join("libperl.so");
        if unversioned.exists() {
            println!("cargo:rustc-link-search=native={}", parent.display());
            println!("cargo:rustc-link-lib=dylib=perl");
        } else {
            let out_dir = std::env::var("OUT_DIR").unwrap();
            let symlink_path = Path::new(&out_dir).join("libperl.so");
            let _ = fs::remove_file(&symlink_path);
            std::os::unix::fs::symlink(&resolved_libperl, &symlink_path)
                .expect("Failed to create libperl.so symlink");
            println!("cargo:rustc-link-search=native={out_dir}");
            println!("cargo:rustc-link-lib=dylib=perl");
        }
    }

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=csrc/perl_glue.c");
}
