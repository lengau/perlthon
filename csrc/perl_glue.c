/*
 * perl_glue.c - C wrapper around the Perl embedding API.
 *
 * Perl's API is heavily macro-based, making direct FFI from Rust impractical.
 * This thin wrapper exposes clean C functions that Rust can call.
 */

#include <EXTERN.h>
#include <perl.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>

/* --- Interpreter lifecycle --- */

PerlInterpreter *perlthon_alloc(void) {
    /* When loaded as a Python extension, libperl's symbols aren't globally
     * visible. XS modules loaded by DynaLoader need them, so we re-open
     * libperl with RTLD_GLOBAL to make its symbols available. */
    dlopen("libperl.so.5.40", RTLD_NOW | RTLD_GLOBAL | RTLD_NOLOAD);
    PerlInterpreter *my_perl = perl_alloc();
    if (my_perl) {
        PERL_SET_CONTEXT(my_perl);
        perl_construct(my_perl);
    }
    return my_perl;
}

/* Forward declaration for the XS init function */
EXTERN_C void xs_init(pTHX);

/* Boot DynaLoader so XS modules can be loaded dynamically */
EXTERN_C void boot_DynaLoader(pTHX_ CV *cv);

EXTERN_C void xs_init(pTHX) {
    static const char file[] = __FILE__;
    dXSUB_SYS;
    newXS("DynaLoader::boot_DynaLoader", boot_DynaLoader, file);
}

int perlthon_init(PerlInterpreter *my_perl) {
    PERL_SET_CONTEXT(my_perl);
    char *embedding[] = {"", "-e", "0"};
    int rc = perl_parse(my_perl, xs_init, 3, embedding, NULL);
    if (rc == 0) {
        rc = perl_run(my_perl);
    }
    return rc;
}

void perlthon_destroy(PerlInterpreter *my_perl) {
    if (my_perl) {
        PERL_SET_CONTEXT(my_perl);
        perl_destruct(my_perl);
        perl_free(my_perl);
    }
}

/* --- eval --- */

/* Evaluate Perl code. Returns an SV* (caller must interpret).
 * Sets *error to the error message if evaluation fails (caller must free). */
SV *perlthon_eval(PerlInterpreter *my_perl, const char *code, char **error) {
    PERL_SET_CONTEXT(my_perl);
    dSP;

    SV *result = eval_pv(code, 0 /* don't croak */);

    /* Check $@ for errors */
    SV *errsv = get_sv("@", 0);
    if (errsv && SvTRUE(errsv)) {
        const char *err = SvPV_nolen(errsv);
        *error = strdup(err);
        return NULL;
    }

    *error = NULL;
    /* Increment refcount so the SV survives beyond the current scope */
    SvREFCNT_inc(result);
    return result;
}

/* --- use module --- */

int perlthon_use_module(PerlInterpreter *my_perl, const char *module_name, char **error) {
    PERL_SET_CONTEXT(my_perl);

    /* Use require + import, checking %INC first to avoid reload errors. */
    char buf[2048];
    snprintf(buf, sizeof(buf),
             "do { my $f = '%s.pm'; $f =~ s|::|/|g;"
             " unless ($INC{$f}) { require $f; %s->import() if %s->can('import'); }"
             " 1; };",
             module_name, module_name, module_name);

    eval_pv(buf, 0);

    SV *errsv = get_sv("@", 0);
    if (errsv && SvTRUE(errsv)) {
        const char *err = SvPV_nolen(errsv);
        *error = strdup(err);
        return -1;
    }
    *error = NULL;
    return 0;
}

/* --- Call a Perl function by fully qualified name --- */

SV *perlthon_call_function(PerlInterpreter *my_perl, const char *func_name,
                            int argc, SV **argv, char **error) {
    PERL_SET_CONTEXT(my_perl);
    dSP;

    ENTER;
    SAVETMPS;

    PUSHMARK(SP);
    for (int i = 0; i < argc; i++) {
        XPUSHs(argv[i]);
    }
    PUTBACK;

    int count = call_pv(func_name, G_SCALAR | G_EVAL);

    SPAGAIN;

    SV *errsv = get_sv("@", 0);
    if (errsv && SvTRUE(errsv)) {
        const char *err = SvPV_nolen(errsv);
        *error = strdup(err);
        PUTBACK;
        FREETMPS;
        LEAVE;
        return NULL;
    }

    SV *result = NULL;
    if (count > 0) {
        result = POPs;
        SvREFCNT_inc(result);
    }

    PUTBACK;
    FREETMPS;
    LEAVE;

    *error = NULL;
    return result;
}

/* --- Call a method on a module/class --- */

SV *perlthon_call_method(PerlInterpreter *my_perl, const char *module,
                          const char *method, int argc, SV **argv, char **error) {
    PERL_SET_CONTEXT(my_perl);
    dSP;

    ENTER;
    SAVETMPS;

    PUSHMARK(SP);
    /* Push the invocant (class name) */
    XPUSHs(sv_2mortal(newSVpv(module, 0)));
    for (int i = 0; i < argc; i++) {
        XPUSHs(argv[i]);
    }
    PUTBACK;

    int count = call_method(method, G_SCALAR | G_EVAL);

    SPAGAIN;

    SV *errsv = get_sv("@", 0);
    if (errsv && SvTRUE(errsv)) {
        const char *err = SvPV_nolen(errsv);
        *error = strdup(err);
        PUTBACK;
        FREETMPS;
        LEAVE;
        return NULL;
    }

    SV *result = NULL;
    if (count > 0) {
        result = POPs;
        SvREFCNT_inc(result);
    }

    PUTBACK;
    FREETMPS;
    LEAVE;

    *error = NULL;
    return result;
}

/* --- SV type introspection and value extraction --- */

/* Returns: 0=undef, 1=int, 2=float, 3=string, 4=arrayref, 5=hashref, 6=other_ref */
int perlthon_sv_type(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    if (!sv || !SvOK(sv)) return 0;  /* undef */
    if (SvROK(sv)) {
        SV *inner = SvRV(sv);
        svtype t = SvTYPE(inner);
        if (t == SVt_PVAV) return 4;  /* arrayref */
        if (t == SVt_PVHV) return 5;  /* hashref */
        return 6;  /* other ref */
    }
    if (SvIOK(sv)) return 1;  /* integer */
    if (SvNOK(sv)) return 2;  /* float */
    return 3;  /* string (fallback) */
}

long long perlthon_sv_iv(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    return (long long)SvIV(sv);
}

double perlthon_sv_nv(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    return SvNV(sv);
}

/* Returns pointer to string and sets *len. Caller must NOT free the pointer. */
const char *perlthon_sv_pv(PerlInterpreter *my_perl, SV *sv, size_t *len) {
    PERL_SET_CONTEXT(my_perl);
    STRLEN l;
    const char *s = SvPV(sv, l);
    *len = (size_t)l;
    return s;
}

/* Array ref accessors */
int perlthon_av_len(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    AV *av = (AV *)SvRV(sv);
    return (int)(av_len(av) + 1);  /* av_len returns highest index */
}

SV *perlthon_av_fetch(PerlInterpreter *my_perl, SV *sv, int index) {
    PERL_SET_CONTEXT(my_perl);
    AV *av = (AV *)SvRV(sv);
    SV **elem = av_fetch(av, index, 0);
    if (elem) {
        SvREFCNT_inc(*elem);
        return *elem;
    }
    return NULL;
}

/* Hash ref accessors */
int perlthon_hv_iterinit(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    HV *hv = (HV *)SvRV(sv);
    return (int)hv_iterinit(hv);
}

/* Returns 1 if got a key/value pair, 0 if done.
 * Sets *key, *klen, and *val. Caller must SvREFCNT_dec val when done. */
int perlthon_hv_iternext(PerlInterpreter *my_perl, SV *sv,
                          const char **key, size_t *klen, SV **val) {
    PERL_SET_CONTEXT(my_perl);
    HV *hv = (HV *)SvRV(sv);
    HE *entry = hv_iternext(hv);
    if (!entry) return 0;

    I32 l;
    *key = hv_iterkey(entry, &l);
    *klen = (size_t)l;
    *val = hv_iterval(hv, entry);
    SvREFCNT_inc(*val);
    return 1;
}

/* --- SV creation helpers --- */

SV *perlthon_new_sv_iv(PerlInterpreter *my_perl, long long val) {
    PERL_SET_CONTEXT(my_perl);
    return sv_2mortal(newSViv((IV)val));
}

SV *perlthon_new_sv_nv(PerlInterpreter *my_perl, double val) {
    PERL_SET_CONTEXT(my_perl);
    return sv_2mortal(newSVnv(val));
}

SV *perlthon_new_sv_pv(PerlInterpreter *my_perl, const char *s, size_t len) {
    PERL_SET_CONTEXT(my_perl);
    return sv_2mortal(newSVpvn(s, len));
}

SV *perlthon_new_sv_bool(PerlInterpreter *my_perl, int val) {
    PERL_SET_CONTEXT(my_perl);
    return sv_2mortal(val ? &PL_sv_yes : &PL_sv_no);
}

SV *perlthon_new_sv_undef(PerlInterpreter *my_perl) {
    PERL_SET_CONTEXT(my_perl);
    return sv_2mortal(newSV(0));
}

void perlthon_sv_decref(PerlInterpreter *my_perl, SV *sv) {
    PERL_SET_CONTEXT(my_perl);
    SvREFCNT_dec(sv);
}

void perlthon_free_error(char *error) {
    free(error);
}
