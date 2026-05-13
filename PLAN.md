# Plan: Bundle Relocatable Perl into Perlthon Wheel

## Problem

Perlthon currently links against the system's `libperl.so` and relies on system-installed Perl modules (POSIX, Scalar::Util, etc.). This means:
- Users need `libperl-dev` installed
- XS modules crash if the system Perl layout doesn't match expectations
- The CI test job crashes with exit code 127 when loading POSIX (likely missing libperl symbols at runtime)

## Approach

Bundle a **relocatable Perl installation** inside the wheel. The wheel will contain:
- `perlthon/_perl/bin/perl` (the interpreter binary — only needed for reference, not execution)
- `perlthon/_perl/lib/` — core Perl modules (.pm + XS .so files)
- `perlthon/_perl/lib/*/CORE/libperl.so` — the shared library
- The perlthon extension (`_core.so`) will link against THIS bundled libperl

### Key architectural decisions:
1. **Build Perl from source** during wheel build (`before-script-linux` in maturin-action)
2. **Configure Perl as relocatable** (`-Duserelocatableinc`) so it finds its libs relative to itself
3. **Statically link libperl** into the extension (avoids LD_LIBRARY_PATH issues) OR bundle the .so and use RPATH
4. **Set PERL5LIB** at runtime to point to the bundled Perl lib directory
5. **Modify `build.rs`** to use the bundled Perl's `ExtUtils::Embed` output instead of the system Perl
6. **Modify `perl_glue.c`** to set `PERL5LIB` before initializing the interpreter

### Static vs dynamic linking:
- **Static linking** (recommended): Compile Perl with `-Duseshrplib=false`, link `libperl.a` into our extension. No runtime path issues. Larger wheel but fully self-contained.
- **Dynamic linking** alternative: Bundle `libperl.so` and use `$ORIGIN` RPATH. More complex.

We'll go with **static linking** of libperl and bundle only the Perl module tree.

## Todos

1. **Makefile** — Create a `Makefile` with targets to:
   - Download Perl 5.40.x source
   - Configure with: `-des -Duserelocatableinc -Dprefix=... -Duseshrplib=false -Doptimize=-O2`
   - Build and install to a staging directory
   - Strip unnecessary files (man pages, pods, documentation)
   - Usage: `make perl PREFIX=/path/to/install`

2. **build.rs** — Update `build.rs` to:
   - Check for `PERLTHON_PERL_PREFIX` env var pointing to the bundled Perl
   - If set, use that Perl for ccopts/ldopts (statically link libperl.a)
   - If unset, fall back to system Perl (development mode)

3. **perl_glue.c** — Update `perlthon_init()` to:
   - At runtime, compute the path to the bundled Perl lib relative to the extension .so
   - Set `PERL5LIB` before calling `perl_parse()`
   - Remove the hardcoded `dlopen("libperl.so.5.40", ...)` (no longer needed with static linking)

4. **__init__.py** — Update to:
   - Expose a `perl_home()` helper that returns the path to the bundled Perl
   - Set `PERL5LIB` environment variable before the first interpreter is created

5. **pyproject.toml** — Update maturin config to include the bundled Perl tree as package data:
   - Add `[tool.maturin] data` or use `include` to bundle `_perl/` directory

6. **CI workflows** — Update wheel build jobs to:
   - Run `make perl` in `before-script-linux`
   - Set `PERLTHON_PERL_PREFIX` environment variable
   - Ensure the Perl tree gets included in the wheel

7. **Tests** — Ensure tests work with bundled Perl (should "just work" if PERL5LIB is set correctly)

## Notes

- Perl 5.40.x source is ~25MB. Compiled with core modules, the installed tree is ~50-80MB. After stripping docs/man/pod, probably ~30-40MB.
- The wheel will be significantly larger than before (~30-40MB per architecture).
- `-Duserelocatableinc` makes Perl find its libraries relative to the binary path — essential for wheel portability.
- We keep the fallback to system Perl for development (so developers don't need to build Perl locally).
- For manylinux compatibility, Perl must be built inside the manylinux container.
