use std::process::Command;

fn main() {
    // Get Perl compiler flags
    let ccopts = Command::new("perl")
        .args(["-MExtUtils::Embed", "-e", "ccopts"])
        .output()
        .expect("Failed to run perl for ccopts — is Perl installed?");
    let ccopts = String::from_utf8(ccopts.stdout).unwrap();

    // Get Perl linker flags
    let ldopts = Command::new("perl")
        .args(["-MExtUtils::Embed", "-e", "ldopts"])
        .output()
        .expect("Failed to run perl for ldopts");
    let ldopts = String::from_utf8(ldopts.stdout).unwrap();

    // Compile the C glue code
    let mut cc = cc::Build::new();
    cc.file("csrc/perl_glue.c");

    // Add compiler flags from Perl
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

    // Suppress warnings from Perl headers
    cc.warnings(false);
    cc.compile("perl_glue");

    // Perl XS modules loaded via DynaLoader need Perl API symbols to be visible.
    // Pass linker flags from ldopts and ensure dynamic symbol export.
    for flag in ldopts.split_whitespace() {
        if flag == "-Wl,-E" {
            println!("cargo:rustc-link-arg=-Wl,-E");
        }
    }
    // Also ensure we export dynamic symbols so DynaLoader'd .so files can resolve Perl symbols
    println!("cargo:rustc-link-arg=-Wl,--export-dynamic");

    // Parse library paths and libs from ldopts
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

    // Handle libperl specially: find the actual .so and create a symlink in OUT_DIR
    // because the system may only have versioned libperl.so.5.x without an unversioned symlink
    if found_perl_lib {
        let out_dir = std::env::var("OUT_DIR").unwrap();

        // Try to find libperl.so (unversioned) first
        let perl_lib_search = Command::new("perl")
            .args([
                "-MConfig",
                "-e",
                r#"print "$Config{archlib}/CORE\n$Config{libpth}""#,
            ])
            .output()
            .expect("Failed to get Perl lib paths");
        let search_paths = String::from_utf8(perl_lib_search.stdout).unwrap();

        let mut found = false;
        for search_dir in search_paths.split_whitespace() {
            let unversioned = format!("{search_dir}/libperl.so");
            if std::path::Path::new(&unversioned).exists() {
                println!("cargo:rustc-link-search=native={search_dir}");
                println!("cargo:rustc-link-lib=dylib=perl");
                found = true;
                break;
            }
        }

        if !found {
            // No unversioned symlink — find the versioned .so and create a symlink in OUT_DIR
            for search_dir in search_paths.split_whitespace() {
                for entry in std::fs::read_dir(search_dir)
                    .into_iter()
                    .flatten()
                    .flatten()
                {
                    let name = entry.file_name();
                    let name = name.to_string_lossy();
                    if name.starts_with("libperl.so.") && !name.ends_with(".1") {
                        let symlink_path = format!("{out_dir}/libperl.so");
                        let _ = std::fs::remove_file(&symlink_path);
                        std::os::unix::fs::symlink(entry.path(), &symlink_path)
                            .expect("Failed to create libperl.so symlink");
                        println!("cargo:rustc-link-search=native={out_dir}");
                        println!("cargo:rustc-link-lib=dylib=perl");
                        found = true;
                        break;
                    }
                }
                if found {
                    break;
                }
            }

            if !found {
                panic!(
                    "Could not find libperl.so — install libperl-dev or ensure Perl development libraries are available"
                );
            }
        }
    }

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=csrc/perl_glue.c");
}
