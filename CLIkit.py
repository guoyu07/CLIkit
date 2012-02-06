#!/usr/local/bin/python
#
# Copyright 2012 Poul-Henning Kamp <phk@FreeBSD.org> 
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# This is a slightly weird Python program:  It writes C-code.
#
# It can be run in two modes:
#
# With the argument "--tree" it will parse a CLI-langauge specification
# and write out a .h and .c file with code to implement that CLI structure.
#
# With the argument "--code" it will write out a .h and .c file that provides
# the infrastructure code necessary for the --tree generated code.
#
# The reason for this split is that you might have multiple invocations
# with --tree in a software project, for instance once for each loadable
# module etc.
#
#
# XXX: "help things 4" doesn't work (Unspecified CLI error.)
# XXX: autodetect colum width for tophelp

from __future__ import print_function

import sys
import os

#######################################################################
#

vtypes = dict()

class vtype(object):
	def __init__(self, name, ctype):
		self.name = name;
		self.c_type = ctype
		self.func = "clikit_int_arg_" + self.name
		vtypes[name] = self

	def ctype(self):
		return self.c_type

	def conv(self, cc, tgt):
		return "%s(%s, %s)" % (self.func, cc, tgt)

	def conv_proto(self):
		return "int %s(struct clikit_context *cc, %s*);" % \
		    (self.func, self.c_type)

	def compare(self, arg):
		if self.c_type in ("double", "int", "unsigned"):
			s = "\tif (a->%s > b->%s)\n" % (arg, arg)
			s += "\t\treturn (1);\n"
			s += "\tif (a->%s < b->%s)\n" % (arg, arg)
			s += "\t\treturn (-1);\n"
			return s
		if self.c_type == "const char *":
			s = "\t{\n"
			s += "\tint i = strcmp(a->%s, a->%s);\n" % (arg, arg)
			s += "\tif (i != 0)\n"
			s += "\t\treturn(i);\n"
			s += "\t}\n"
			return (s)
		assert "Missing" == "Vtype compare function"

vtype("REAL", "double")
vtype("UINT", "unsigned")
vtype("INT", "int")
vtype("WORD", "const char *")


#######################################################################
#

def usage(txt = None):
	if txt != None:
		sys.stderr.write("Error: " + txt + "\n")
	sys.stderr.write("""Usage:
	CLIkit.py --code [-o basename] [opts]
		Emit the CLIkit implementation to basename.[ch]

	CLIkit.py --tree foo.clikit [opts]
		Compile foo.clikit to foo.[ch]
""")
	exit(2)

#######################################################################
#

def do_copyright(fd):
	fd.write("""/*
 * Copyright 2012 Poul-Henning Kamp <phk@FreeBSD.org> 
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * NB: This file is generated by CLIkit.py: *** Do Not Edit By Hand ***
 */

""")

def do_code(argv):
	pfx = "clikit"
	if len(argv) > 0 and argv[0] == "-o":
		if len(argv) < 2:
			usage()
		pfx = argv[1]
		argv = argv[2:]
	print("DO_CODE", "PFX=%s" % pfx, argv)
	if len(argv) > 0:
		usage("XXX: no options supported yet")

	fo = open(pfx + ".h", "w")
	do_copyright(fo)
	fo.write("""
#ifndef __CLIKIT_H__
#define __CLIKIT_H__

#include <stdarg.h>

struct clikit;
struct clikit_context;

/*---------------------------------------------------------------------
 * The type of generated codes named entrypoints
 *
 * XXX: rename to "clikit_branch"
 */
typedef int clikit_match_f(struct clikit_context *);

/*---------------------------------------------------------------------
 * Management of CLIkit instances
 *
 * Your basic New/Destroy API, I don't need to explain this, right ?
 */

struct clikit * CLIkit_New(void);
int CLIkit_Destroy(struct clikit *);
/* XXX: error_handling() */

/*---------------------------------------------------------------------
 * Management of command prefixes ("help", "show" etc.)
 *
 * Prefixes are things like "help", "show", "enable", "disable" you
 * want to be able to put in front of every command in your language.
 *
 * Which prefixes are present are communicated in a bit map you can
 * get with CLIkit_GetPrefix() (see below)
 *
 * Prefix value 1 is the help prefix and it does weird and wonderful
 * things other prefixes do not do.
 *
 * You get to define the bitmap values and prefixes with these two
 * functions:
 */

int CLIkit_Add_Prefix(struct clikit *, const char *pfx, unsigned val);
int CLIkit_Add_Prefix_Recurse(struct clikit *, const char *pfx, unsigned val);
int CLIkit_Del_Prefix(const struct clikit *, const char *pfx);

/*---------------------------------------------------------------------
 * Management of command branches.
 *
 * Use these functions to add/delete branches from the --tree files
 * you have compiled.
 *
 * You can prefix a branch with a "root" so that you can avoid
 * duplication.
 *
 * XXX: rename to Add/Del_Branch
 * XXX: add priv arg.
 */
int CLIkit_Add_Tree(struct clikit *, clikit_match_f *func, const char *root);
int CLIkit_Del_Tree(const struct clikit *, clikit_match_f *func,
    const char *root);

/*---------------------------------------------------------------------
 * Management of sessions.
 *
 * A session is a source of cli commands, stdin, a TCP socket or a file.
 */
struct clikit_context *CLIkit_New_Context(struct clikit *);
int CLIkit_Destroy_Context(struct clikit_context *);

/*
 * Configure a string output function
 *
 * This function is called a number of times for each CLI command executed.
 * Last time with a NULL 'str' argument, to signal end of the transaction.
 *
 * The error argument is zero by default, '-1' if an error originates
 * inside CLIkit and comes from CLIkit_Error() (see below) in all other cases.
 *
 * If no function is registered, the default function sends output to stdout.
 *
 * A return value less than zero means "stop generating output" for whatever
 * reason the function might have for this sentiment.
 */
typedef int clikit_puts_f(void *priv, int error, const char *str);
void CLIkit_Set_Puts(struct clikit_context *, clikit_puts_f *func, void *priv);

/* Inject bytes into CLI interpreter */
void CLIkit_Input(struct clikit_context *, const char *);

/*---------------------------------------------------------------------
 * Functions to call from the command implementation functions
 */

int CLIkit_Error(struct clikit_context *, int error, const char *fmt, ...);
int CLIkit_Puts(const struct clikit_context *, const char *str);
int CLIkit_Printf(const struct clikit_context *, const char *fmt, ...);
unsigned CLIkit_Get_Prefix(const struct clikit_context *);
void *CLIkit_Get_Instance(const struct clikit_context *);

#ifdef CLIKIT_INTERNAL
/*
 * Helper functions for used by the code generated with --tree.
 */

int clikit_int_match(struct clikit_context *, const char *);
int clikit_int_help(const struct clikit_context *, const char *);
int clikit_int_tophelp(const struct clikit_context *, const char *,
    const char *);
int clikit_int_eol(const struct clikit_context *);
int clikit_int_recurse(const struct clikit_context *);
// void clikit_int_push_instance(struct clikit_context *);
// void clikit_int_pop_instance(struct clikit_context *);
int clikit_int_unknown(struct clikit_context *);

typedef int clikit_recurse_f(struct clikit_context *);
int clikit_int_stdinstance(struct clikit_context *, clikit_recurse_f *,
    const char *, const char *);

typedef int clikit_compare_f(const void *, const void *);

void clikit_int_findinstance(struct clikit_context *, void *, const void *,
    clikit_compare_f*);
void clikit_int_addinstance(struct clikit_context *, const void *,
    const void *ident, unsigned long);

""")
	for i,j in vtypes.iteritems():
		fo.write(j.conv_proto() + "\n")
	fo.write("""

/********************************************************************
 * From FreeBSD's <sys/queue.h>
 * Copyright (c) 1991, 1993
 *	The Regents of the University of California.  All rights reserved.
 */

#define	CKL_HEAD(name, type)						\\
struct name {								\\
	struct type *lh_first;	/* first element */			\\
}

#define	CKL_ENTRY(type)							\\
struct {								\\
	struct type *le_next;	/* next element */			\\
	struct type **le_prev;	/* address of previous next element */	\\
}

#define	CKL_FIRST(head)	((head)->lh_first)

#define	CKL_FOREACH(var, head, field)					\\
	for ((var) = CKL_FIRST((head));					\\
	    (var);							\\
	    (var) = CKL_NEXT((var), field))

/*lint -emacro(506, CKL_FOREACH_SAFE) */

#define	CKL_FOREACH_SAFE(var, head, field, tvar)			\\
	for ((var) = CKL_FIRST((head));					\\
	    (var) && ((tvar) = CKL_NEXT((var), field), 1);		\\
	    (var) = (tvar))


#define	CKL_INIT(head) do {						\\
	CKL_FIRST((head)) = NULL;					\\
} while (0)

#define	CKL_INSERT_HEAD(head, elm, field) do {				\\
	if ((CKL_NEXT((elm), field) = CKL_FIRST((head))) != NULL)	\\
		CKL_FIRST((head))->field.le_prev = &CKL_NEXT((elm), field);\\
	CKL_FIRST((head)) = (elm);					\\
	(elm)->field.le_prev = &CKL_FIRST((head));			\\
} while (0)

#define	CKL_NEXT(elm, field)	((elm)->field.le_next)

#define	CKL_REMOVE(elm, field) do {					\\
	if (CKL_NEXT((elm), field) != NULL)				\\
		CKL_NEXT((elm), field)->field.le_prev = 		\\
		    (elm)->field.le_prev;				\\
	*(elm)->field.le_prev = CKL_NEXT((elm), field);			\\
} while (0)

struct clikit_instance {
	CKL_ENTRY(clikit_instance)	list;
	const void			*ident;
	void				*ptr;
};

#endif /* CLIKIT_INTERNAL */

#endif /* __CLIKIT_H__ */
""")
	fo.close()

	fo = open(pfx + ".c", "w")
	do_copyright(fo)
	fo.write("""

/*********************************************************************/

#include <assert.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CLIKIT_INTERNAL
""")
	fo.write("#include \"%s.h\"\n" % pfx)
	fo.write("""

/*********************************************************************/

struct clikit_prefix;
struct clikit_branch;

struct clikit {
	unsigned			magic;
#define CLIKIT_MAGIC			0x6c5315b8
	CKL_HEAD(, clikit_branch)	branches;
	CKL_HEAD(, clikit_prefix)	prefixes;
	CKL_HEAD(, clikit_context)	contexts;
};

struct clikit_branch {
	unsigned			magic;
#define CLIKIT_BRANCH_MAGIC		0x21031be5
	CKL_ENTRY(clikit_branch)	list;
	clikit_match_f			*func;
	char				*root;
};

struct clikit_prefix {
	unsigned			magic;
#define CLIKIT_PREFIX_MAGIC		0xb793beea
	CKL_ENTRY(clikit_prefix)	list;
	char				*pfx;
	unsigned			val;
	char				recurse;
};

struct clikit_context {
	unsigned			magic;
#define CLIKIT_CONTEXT_MAGIC		0xa70f836a
	struct clikit			*ck;
	CKL_ENTRY(clikit_context)	list;
	char				*b;
	char				*e;
	char				*p;
	enum {
		sIdle,
		sComment,
		sWord,
		sQuoted,
		sBackslash
	}				st;
	unsigned			prefix;
	int				help;
	int				recurse;

	int				error;

	struct clikit_instance		*cur_instance;
	CKL_HEAD(,clikit_instance)	instances;

	/* "Puts" handler */
	clikit_puts_f			*puts_func;
	void				*puts_priv;
	int				puts_int;
};

/*********************************************************************/

struct clikit *
CLIkit_New(void)
{
	struct clikit *ck;

	ck = calloc(1L, sizeof *ck);
	if (ck == NULL)
		return (ck);
	ck->magic = CLIKIT_MAGIC;
	CKL_INIT(&ck->branches);
	CKL_INIT(&ck->prefixes);
	CKL_INIT(&ck->contexts);
	return (ck);
}

int
CLIkit_Destroy(struct clikit *ck)
{
	struct clikit_branch *cb, *cb2;
	struct clikit_prefix *cp, *cp2;
	struct clikit_context *cc, *cc2;
	int retval = 0;

	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);

	CKL_FOREACH_SAFE(cc, &ck->contexts, list, cc2) {
		assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
		retval |= CLIkit_Destroy_Context(cc);
	}
		
	CKL_FOREACH_SAFE(cb, &ck->branches, list, cb2) {
		assert(cb != NULL && cb->magic == CLIKIT_BRANCH_MAGIC);
		retval |= CLIkit_Del_Tree(ck, cb->func, cb->root);
	}
		
	CKL_FOREACH_SAFE(cp, &ck->prefixes, list, cp2) {
		assert(cp != NULL && cp->magic == CLIKIT_PREFIX_MAGIC);
		retval |= CLIkit_Del_Prefix(ck, cp->pfx);
	}

	free(ck);
	return (retval);
}

/*********************************************************************/

static struct clikit_prefix *
clikit_add_prefix(struct clikit *ck, const char *pfx, unsigned val)
{
	struct clikit_prefix *cp;
	struct clikit_branch *cb;

	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);

	if (val == 0 && strcmp(pfx, "help")) {
		/* Only "help" is allowed to have zero value */
		return (NULL);
	}

	CKL_FOREACH(cp, &ck->prefixes, list) {
		/* XXX: return -1 + errno */
		assert(strcmp(cp->pfx, pfx));
		assert(cp->val != val);
	}
	CKL_FOREACH(cb, &ck->branches, list) {
		/* XXX: return -1 + errno */
		assert(cb->root == NULL || strcmp(cb->root, pfx));
	}

	cp = calloc(1L, sizeof *cp);
	if (cp == NULL)
		return (NULL);
	cp->magic = CLIKIT_PREFIX_MAGIC;
	cp->val = val;
	cp->pfx = strdup(pfx);
	if (cp->pfx == NULL) {
		free(cp);
		return (NULL);
	}
	CKL_INSERT_HEAD(&ck->prefixes, cp, list);
	return (cp);
}

int
CLIkit_Add_Prefix(struct clikit *ck, const char *pfx, unsigned val)
{
	struct clikit_prefix *cp;

	cp = clikit_add_prefix(ck, pfx, val);
	if (cp == NULL)
		return (-1);
	return (0);
}

int
CLIkit_Add_Prefix_Recurse(struct clikit *ck, const char *pfx, unsigned val)
{
	struct clikit_prefix *cp;

	cp = clikit_add_prefix(ck, pfx, val);
	if (cp == NULL)
		return (-1);
	cp->recurse = 1;
	return (0);
}

int
CLIkit_Del_Prefix(const struct clikit *ck, const char *pfx)
{
	struct clikit_prefix *cp;
	
	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);
	CKL_FOREACH(cp, &ck->prefixes, list) {
		assert(cp != NULL && cp->magic == CLIKIT_PREFIX_MAGIC);
		if (!strcmp(cp->pfx, pfx)) {
			CKL_REMOVE(cp, list);
			free(cp->pfx);
			free(cp);
			return (0);
		}
	}
	return (-1);
}

/*********************************************************************/

int
CLIkit_Add_Tree(struct clikit *ck, clikit_match_f *func,
    const char *root)
{
	struct clikit_branch *cb;
	struct clikit_prefix *cp;

	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);

	if (root != NULL) {
		CKL_FOREACH(cp, &ck->prefixes, list)
			assert(strcmp(cp->pfx, root));
		CKL_FOREACH(cb, &ck->branches, list)
			assert(cb->root == NULL || strcmp(cb->root, root));
	}
	cb = calloc(1L, sizeof *cb);
	if (cb == NULL)
		return (-1);
	cb->magic = CLIKIT_BRANCH_MAGIC;
	cb->func = func;
	if (root != NULL) {
		cb->root = strdup(root);
		if (cb->root == NULL) {
			free(cb);
			return (-1);
		}
	}
	CKL_INSERT_HEAD(&ck->branches, cb, list);
	return (0);
}

int
CLIkit_Del_Tree(const struct clikit *ck, clikit_match_f *func,
    const char *root)
{
	struct clikit_branch *cb;
	
	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);
	CKL_FOREACH(cb, &ck->branches, list) {
		assert(cb != NULL && cb->magic == CLIKIT_BRANCH_MAGIC);
		if (cb->func != func)
			continue;
		if (cb->root == NULL && root == NULL)
			;
		else if (cb->root == NULL || root == NULL)
			continue;
		else if (strcmp(cb->root, root)) 
			continue;

		CKL_REMOVE(cb, list);
		free(cb->root);
		free(cb);
		return (0);
	}
	return (-1);
}

/*********************************************************************/

struct clikit_context *
CLIkit_New_Context(struct clikit *ck)
{
	struct clikit_context *cc;

	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);

	cc = calloc(1L, sizeof *cc);
	if (cc == NULL)
		return (NULL);
	cc->magic = CLIKIT_CONTEXT_MAGIC;
	cc->ck = ck;
	cc->b = malloc(64L);
	if (cc->b == NULL) {
		free(cc);
		return (NULL);
	}
	cc->e = cc->b + 64;
	cc->p = cc->b;
	cc->st = sIdle;
	CKL_INIT(&cc->instances);
	CKL_INSERT_HEAD(&ck->contexts, cc, list);

	CLIkit_Set_Puts(cc, NULL, NULL);
	return (cc);
}

int
CLIkit_Destroy_Context(struct clikit_context *cc)
{
	struct clikit *ck;
	
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	ck = cc->ck;
	assert(ck != NULL && ck->magic == CLIKIT_MAGIC);
	CKL_REMOVE(cc, list);
	(void)memset(cc, 0, sizeof *cc);
	free(cc);
	return (0);
}

/**********************************************************************/

int
CLIkit_Error(struct clikit_context *cc, int error, const char *fmt, ...)
{
	va_list ap;
	int retval;
	char *s = NULL;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	cc->error = error;
	va_start(ap, fmt);
	retval = vasprintf(&s, fmt, ap);
	if (retval != -1)
		retval = cc->puts_func(cc->puts_priv, error, s);
	va_end(ap);
	return (retval);
}

int
CLIkit_Puts(const struct clikit_context *cc, const char *str)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	return (cc->puts_func(cc->puts_priv, cc->error, str));
}

int
CLIkit_Printf(const struct clikit_context *cc, const char *fmt, ...)
{
	va_list ap;
	int retval;
	char *s = NULL;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	va_start(ap, fmt);
	retval = vasprintf(&s, fmt, ap);
	if (retval != -1)
		retval = cc->puts_func(cc->puts_priv, cc->error, s);
	va_end(ap);
	return (retval);
}

unsigned
CLIkit_Get_Prefix(const struct clikit_context *cc)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	return (cc->prefix);
}

void *
CLIkit_Get_Instance(const struct clikit_context *cc)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	return (cc->cur_instance->ptr);
}

/*********************************************************************
 * Puts and default function
 */

static int
clikit_default_puts(void *priv, int error, const char *str)
{
	int *pp = priv;
	int retval = 0;

	if (str == NULL) {
		*pp = 0;
	} else {
		if (*pp != error)
			(void)printf("ERROR %d:\\n", error);
		*pp = error;
		if (fputs(str, stdout) == EOF)
			retval = -1;
	}
	return (retval);
}

void
CLIkit_Set_Puts(struct clikit_context *cc, clikit_puts_f *func, void *priv)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);

	if (func == NULL) {
		func = clikit_default_puts;
		priv = &cc->puts_int;
	}
	cc->puts_func = func;
	cc->puts_priv = priv;
}

/*********************************************************************
 * Add one character to our buffer, extend as necessary.
 */

static void
clikit_add_char(struct clikit_context *cc, int ch)
{
	size_t l;
	char *p;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(cc->b < cc->e);
	assert(cc->p >= cc->b);
	assert(cc->p <= cc->e);

	if (cc->p == cc->e) {
		l = cc->e - cc->b;	/*lint !e732*/
		if (l > 4096L)
			l += 4096L;
		else
			l += l;
		p = realloc(cc->b, l);
		/* XXX: p */
		assert(p != NULL);
		cc->p = p + (cc->p - cc->b);
		cc->b = p;
		cc->e = p + l;
	}
	assert(cc->p >= cc->b);
	assert(cc->p < cc->e);
	*cc->p = (char)ch;
	cc->p++;
}

/*********************************************************************
 *
 */

int
clikit_int_stdinstance(struct clikit_context *cc, clikit_recurse_f *rf,
   const char *h1, const char *h2)
{
	struct clikit_instance *id, *id2;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(rf != NULL);

	/* If Help prefix:  Recurse without instance */
	if ((cc->prefix & 1)) {
		if (CLIkit_Printf(cc, "%*s%-*s %s\\n",
		    cc->help * 2, "", 30 - cc->help * 2, h1, h2))
			return (1);
		cc->help++;
		cc->cur_instance = NULL;
		(void)rf(cc);
		cc->help--;
		return (1);
	}

	/* Recursion at end of command:  Walk through all instances */
	if (cc->recurse && clikit_int_eol(cc)) {
		CKL_FOREACH_SAFE(id, &cc->instances, list, id2) {
			if (id->ident != rf)
				continue;
			cc->cur_instance = id;
			(void)rf(cc);
		}
		return (1);
	}

	if (clikit_int_eol(cc)) {
		(void)CLIkit_Error(cc, -1, "Incomplete command\\n");
		return (-1);
	}
	return (0);
}

/*********************************************************************
 */

void
clikit_int_findinstance(struct clikit_context *cc, void *ip, const void *ident,
    clikit_compare_f *func)
{
	struct clikit_instance *id, *id2;
	id2 = ip;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);

	CKL_FOREACH(id, &cc->instances, list) {
		if (id->ident != ident)
			continue;
		if (func(id, ip) == 0) {
			id2->ptr = id->ptr;
			cc->cur_instance = id;
			return;
		}
	}

}

/*********************************************************************
 */

void
clikit_int_addinstance(struct clikit_context *cc, const void *ptr,
    const void *ident, unsigned long len)
{
	struct clikit_instance *id;
	void *p;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);

	p = calloc(1L, len);
	assert(p != 0);
	(void)memcpy(p, ptr, len);
	id = p;
	id->ident = ident;
	CKL_INSERT_HEAD(&cc->instances, id, list);
	cc->cur_instance = id;
}

/*********************************************************************
 */

int
clikit_int_tophelp(const struct clikit_context *cc, const char *s1,
    const char *s2)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	if (cc->help == 0)
		return (0);
	(void)CLIkit_Printf(cc, "%*s%-*s %s\\n",
	    cc->help * 2, "",
	    30 - cc->help * 2, s1, s2);
	return (1);
}

static void
clikit_top_help(struct clikit_context *cc)
{
	struct clikit_branch *cb;

	cc->help = 1;
	CKL_FOREACH(cb, &cc->ck->branches, list) {
		if (cb->root) {
			(void)CLIkit_Printf(cc, "%*s%s:\\n",
			    cc->help * 2, "", cb->root);
			cc->help++;
		}
		(void)cb->func(cc);
		if (cb->root) 
			cc->help--;
	}
}


/*********************************************************************
 * We have a complete command, execute it.
 */

static void
clikit_next(struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(*cc->p);
	cc->p += strlen(cc->p) + 1;
}

static int
clikit_is_prefix(struct clikit_context *cc)
{
	struct clikit_prefix *cp;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(cc->ck != NULL && cc->ck->magic == CLIKIT_MAGIC);
	CKL_FOREACH(cp, &cc->ck->prefixes, list) {
		if (strcmp(cc->p, cp->pfx))
			continue;
		if (cc->recurse && cp->recurse) {
			(void)CLIkit_Error(cc, -1,
			    "Clash of incompatible prefixes\\n");
			return (-1);
		}
		cc->recurse = cp->recurse;
		cc->prefix |= cp->val;
		return (1);
	}
	return (0);
}

static void
clikit_exec(struct clikit_context *cc)
{
	struct clikit_branch *cb;
	int i;

	/* Terminate the list */
	clikit_add_char(cc, 0);
	
	cc->p = cc->b;
	cc->help = 0;
	cc->prefix = 0;
	cc->error = 0;
	cc->recurse = 0;
	do {
		i = clikit_is_prefix(cc);
		if (i == -1)
			return;
		if (i == 1)
			clikit_next(cc);
	} while (i == 1);
	if (!*cc->p && (cc->prefix & 1))
		clikit_top_help(cc);
	else if (!*cc->p)
		(void)CLIkit_Error(cc, -1,
		    "Found prefixes but no command\\n");
	else {
		i = -1;
		CKL_FOREACH(cb, &cc->ck->branches, list) {
			if (cb->root != NULL) {
				if (strcmp(cc->p, cb->root))
					continue;
				clikit_next(cc);
			}
			i = cb->func(cc);
			if (i)
				break;
		}
		if (i == 0)
			(void)CLIkit_Error(cc, -1,
			    "Unknown command.\\n");
	}
	if (i == -1 && cc->error != i)
		(void)CLIkit_Error(cc, -1,
		    "Unspecified CLI error.\\n");
}

static void
clikit_complete(struct clikit_context *cc)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(cc->ck != NULL && cc->ck->magic == CLIKIT_MAGIC);

	if (cc->p != cc->b)
		clikit_exec(cc);
	(void)cc->puts_func(cc->puts_priv, cc->error, NULL);
	cc->p = cc->b;
	cc->st = sIdle;
}

/*********************************************************************
 * Move the next char through the state machine
 */

static void
clikit_in_char(struct clikit_context *cc, int ch)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);

	switch(cc->st) {
	case sIdle:
		if (ch == '#')
			cc->st = sComment;
		else if (isspace(ch) && !isblank(ch))
			clikit_complete(cc);
		else if (isspace(ch)) 
			cc->st = sIdle;
		else if (ch == '"')
			cc->st = sQuoted;
		else {
			cc->st = sWord;
			clikit_add_char(cc, ch);
		}
		break;
	case sWord:
		if (isspace(ch)) {
			clikit_add_char(cc, 0);
			cc->st = sIdle;
			if (!isblank(ch))
				clikit_complete(cc);
		} else 
			clikit_add_char(cc, ch);
		break;
	case sQuoted:
		if (ch == '"') {
			clikit_add_char(cc, 0);
			cc->st = sIdle;
		} else if (ch == '\\\\') {
			cc->st = sBackslash;
		} else if (isspace(ch) && !isblank(ch)) {
			(void)CLIkit_Error(cc, -1, "Unterminated quotes\\n");
			cc->p = cc->b;
			cc->st = sIdle;
		} else {
			clikit_add_char(cc, ch);
		}
		break;
	case sBackslash:
		if (ch == 'n')
			clikit_add_char(cc, '\\n');
		else
			clikit_add_char(cc, ch);
		cc->st = sQuoted;
		break;
	case sComment:
		if (isblank(ch))
			;
		else if (isspace(ch))
			cc->st = sIdle;
		break;
	default:
		break;
	}  
}

/*********************************************************************/

void
CLIkit_Input(struct clikit_context *cc, const char *s)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	while (*s != 0)
		clikit_in_char(cc, *s++);
}

/*********************************************************************/

int
clikit_int_help(const struct clikit_context *cc, const char *str)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	if (*cc->p == 0 && (cc->prefix & 1)) {
		(void)CLIkit_Puts(cc, str);
		(void)CLIkit_Puts(cc, "\\n");
		return (1);
	}
	return (0);
}

int
clikit_int_match(struct clikit_context *cc, const char *str)
{

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	if (strcmp(cc->p, str))
		return (1);
	clikit_next(cc);
	return (0);
}

int
clikit_int_eol(const struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	if (*cc->p == 0)
		return (1);
	return (0);
}

int
clikit_int_recurse(const struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	return (cc->recurse);
}

#if 0
void
clikit_int_push_instance(struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	(void)printf("%s()\\n", __func__);
}

void
clikit_int_pop_instance(struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	(void)printf("%s()\\n", __func__);
}
#endif

int
clikit_int_unknown(struct clikit_context *cc)
{
	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	(void)CLIkit_Error(cc, -1, "Unknown command\\n");
	return (-1);
}

int
clikit_int_arg_REAL(struct clikit_context *cc, double *arg)
{
	double d;
	char *q = NULL;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(arg != NULL);
	if (!*cc->p) {
		(void)CLIkit_Error(cc, -1, "Missing REAL argument\\n");
		return (-1);
	}
	d = strtod(cc->p, &q);
	if (*q != 0) {
		(void)CLIkit_Error(cc, -1, "Invalid REAL argument\\n");
		return (-1);
	}
	*arg = d;
	clikit_next(cc);
	return (0);
}

int
clikit_int_arg_INT(struct clikit_context *cc, int *arg)
{
	unsigned long ul;
	char *q = NULL;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(arg != NULL);
	if (!*cc->p) {
		(void)CLIkit_Error(cc, -1, "Missing INT argument\\n");
		return (-1);
	}
	ul = strtoul(cc->p, &q, 0);
	if (*q != 0) {
		(void)CLIkit_Error(cc, -1, "Invalid INT argument\\n");
		return (-1);
	}
	if ((unsigned long)(int)ul != ul) {
		(void)CLIkit_Error(cc, -1, "Too big INT argument\\n");
		return (-1);
	}
	*arg = (int)ul;
	clikit_next(cc);
	return (0);
}

int
clikit_int_arg_UINT(struct clikit_context *cc, unsigned *arg)
{
	unsigned long ul;
	char *q = NULL;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	assert(arg != NULL);
	if (!*cc->p) {
		(void)CLIkit_Error(cc, -1, "Missing UINT argument\\n");
		return (-1);
	}
	ul = strtoul(cc->p, &q, 0);
	if (*q != 0) {
		(void)CLIkit_Error(cc, -1, "Invalid UINT argument\\n");
		return (-1);
	}
	if ((unsigned long)(unsigned)ul != ul) {
		(void)CLIkit_Error(cc, -1, "Too big UINT argument\\n");
		return (-1);
	}
	*arg = (unsigned)ul;
	clikit_next(cc);
	return (0);
}

int
clikit_int_arg_WORD(struct clikit_context *cc, const char **arg)
{
	char *p;

	assert(cc != NULL && cc->magic == CLIKIT_CONTEXT_MAGIC);
	for (p = cc->p; *p; p++)
		if (!isalnum(*p) && *p != '_') {
			(void)CLIkit_Error(cc, -1, "Invalid WORD argument\\n");
			return (-1);
		}
	*arg = cc->p;
	clikit_next(cc);
	return (0);
}


""")

#######################################################################
#######################################################################
#

import shlex

def syntax(foo):
	sys.stderr.write("Syntax Error:\n\t" + foo + "\n")
	exit(2)

def keyval(kv, tl, id):
	assert len(tl) > 0
	if not tl[0] in kv:
		return False
	i = tl.pop(0)
	if kv[i] != None:
		syntax("Multiple '%s' in %s" % (i, id))
	if len(tl) == 0:
		syntax("Missing value '%s' %s" % (i, id))
	kv[i] = tl.pop(0)
	return True

def parse_arglist(tl):
	tal = list()
	while len(tl) > 0 and tl[0] != "{":
		if tl[0] not in vtypes:
			syntax("Bad type '%s' in LEAF(%s)" % (tl[0], nm))
		tal.append(vtypes[tl.pop(0)])
	return tal

def parse_leaf(tl, fc, fh):
	assert tl.pop(0) == "LEAF"
	nr = len(tl)
	nm = tl.pop(0)

	fh.write("/* At token %d LEAF %s */\n" % (nr, nm))
	fc.write("\n/* At token %d LEAF %s */\n" % (nr, nm))

	tal = parse_arglist(tl)
	if len(tl) == 0:
		syntax("Missing '{' in LEAF(%s)" % nm)
	assert tl.pop(0) == "{"
	kv = {
		"desc":	None,
		"func": None,
		"name": None,
	}
	while len(tl) > 0 and tl[0] != "}":
		if keyval(kv, tl, "LEAF(%s)" % nm):
			continue
		else:
			syntax("Unknown '%s' in LEAF(%s)" % (tl[0], nm))
	if len(tl) == 0:
		syntax("Missing '}' in LEAF(%s)" % nm)
	assert tl.pop(0) == "}"

	if kv['desc'] == None:
		kv['desc'] = "(no description)"
	if kv['name'] == None:
		kv['name'] = "match_%d" % nr
		static = "static "
	else:
		static = ""
		fh.write("int %s(struct clikit_context*);\n" % kv['name'])

	if kv['func'] == None:
		syntax("Missing 'func' in LEAF(%s)" % nm)

	print("Leaf(%d, %s)" % (nr, nm), tal, kv)

	fh.write("void %s(struct clikit_context *" % kv["func"])
	for i in tal:
		fh.write(", " + i.ctype())
	fh.write(");\n\n")

	fc.write(static + "int\n%s(struct clikit_context *cc)\n" % kv['name'])
	fc.write('{\n')
	n = 0
	for i in tal:
		fc.write("\t%s arg_%d = 0;\n" % (i.ctype(), n))
		n += 1
	fc.write("\n")	
	s = ''
	for i in tal:
		s += " <" + i.name + ">"
	fc.write('\tif (clikit_int_tophelp(cc, "%s%s", "%s"))\n' %
		(nm, s, kv['desc']))
	fc.write('\t\treturn(0);\n')

	fc.write('\tif (clikit_int_eol(cc) && clikit_int_recurse(cc)) {\n')
	fc.write('\t\t%s(cc' % kv['func'])
	n = 0
	for i in tal:
		fc.write(", arg_%d" % n)
		n += 1
	fc.write(");\n")
	fc.write('\t\treturn(0);\n')
	fc.write('\t}\n')

	fc.write('\tif (clikit_int_match(cc, "%s"))\n\t\treturn(0);\n' % nm)

	fc.write('\tif (clikit_int_help(cc, "%s: %s"))\n' % (nm, kv['desc']))
	fc.write('\t\treturn(1);\n')

	n = 0
	for i in tal:
		fc.write('\tif (%s)\n' % i.conv("cc", "&arg_%d" % n))
		fc.write('\t\treturn(-1);\n')
		n += 1
	fc.write('\tif (!clikit_int_eol(cc))\n\t\treturn(-1);\n')
	fc.write('\t%s(cc' % kv['func'])
	n = 0
	for i in tal:
		fc.write(", arg_%d" % n)
		n += 1
	fc.write(");\n")
	fc.write("\treturn(1);\n")
	fc.write("}\n")

	return kv['name']
	

def parse_instance(tl, fc, fh):
	assert tl.pop(0) == "INSTANCE"
	nr = len(tl)
	nm = tl.pop(0)

	tal = parse_arglist(tl)
	if len(tl) == 0:
		syntax("Missing '{' in INSTANCE(%s)" % nm)
	assert tl.pop(0) == "{"
	children = list()
	kv = {
		"desc":	None,
		"func": None,
		"name": None,
	}
	while len(tl) > 0 and tl[0] != "}":
		if keyval(kv, tl, "INSTANCE(%s)" % nm):
			continue
		elif tl[0] == "LEAF":
			children.append(parse_leaf(tl, fc, fh))
		elif tl[0] == "INSTANCE":
			children.append(parse_instance(tl, fc, fh))
		else:
			syntax("Unknown '%s' in INSTANCE(%s)" % (tl[0], nm))
	if len(tl) == 0:
		syntax("Missing '}' in LEAF(%s)" % nm)
	assert tl.pop(0) == "}"

	fh.write("/* At token %d INSTANCE %s */\n" % (nr, nm))
	fc.write("\n/* At token %d INSTANCE %s */\n" % (nr, nm))

	###############################################################
	# Emit instance struct

	ivs = "i_%d" % nr
	fc.write("struct %s {\n" % ivs)
	fc.write("\tstruct clikit_instance	instance;\n")
	n = 0
	for i in tal:
		fc.write("\t%s\t\targ_%d;\n" % (i.ctype(), n));
		n += 1
	fc.write("};\n\n")

	###############################################################
	# XXX: emit sorting function

	fc.write("static int\n")
	fc.write("compare_%d(const void *aa, const void *bb)\n" % nr)
	fc.write("{\n")
	fc.write("\tconst struct %s *a = aa;\n" % ivs)
	fc.write("\tconst struct %s *b = bb;\n" % ivs)
	fc.write("\t\n")
	n = 0
	for i in tal:
		fc.write(i.compare("arg_%d" % n))
		n += 1
	fc.write("\treturn(0);\n")
	fc.write("}\n\n")

	###############################################################
	# Emit recurse function

	fc.write("static int\n")
	fc.write("recurse_%d(struct clikit_context *cc)\n" % nr)
	fc.write("{\n")
	fc.write("\tint retval;\n")
	fc.write("\n")
	s = ""
	for i in children:
		print(i)
		fc.write("\t" + s)
		fc.write("if ((retval = %s(cc)) != 0) /*lint !e838*/\n" % i)
		fc.write("\t\t;\n")
		s = "else "
	fc.write("\telse if (CLIkit_Get_Prefix(cc) & 1)\n")
	fc.write("\t\tretval = 1;\n")
	fc.write("\telse if (clikit_int_recurse(cc))\n")
	fc.write("\t\tretval = 1;\n")
	fc.write("\telse\n")
	fc.write("\t\tretval = clikit_int_unknown(cc);\n")
	fc.write("\treturn (retval);\n")
	fc.write("}\n");
	fc.write("\n");

	###############################################################
	# Emit function prototype

	if kv['func'] == None:
		syntax("Missing 'func' in LEAF(%s)" % nm)

	fh.write("int %s(struct clikit_context *" % kv["func"])
	for i in tal:
		fh.write(", %s" % i.ctype());
	fh.write(", void **);\n\n")

	###############################################################
	# Emit match function

	if kv['desc'] == None:
		kv['desc'] = "(no description)"
	if kv['name'] == None:
		kv['name'] = "match_%d" % nr
		static = "static "
	else:
		static = ""
		fh.write("int %s(struct clikit_context*);\n" % kv['name'])

	fc.write(static + "int\n%s(struct clikit_context *cc)\n" % kv['name'])
	fc.write('{\n')
	fc.write('\tint retval;\n')
	fc.write('\tstruct %s ivs;\n' % ivs)
	fc.write("\n")	

	s = nm
	for i in tal:
		s += " <" + i.name + ">"
	s += ":"

	fc.write('\tretval = clikit_int_stdinstance(cc, recurse_%d,\n' % nr)
	fc.write('\t    \"%s\", \"%s\");\n' % (s,kv['desc']))
	fc.write('\tif (retval)\n\t\treturn (retval);\n\n')

	fc.write('\tif (clikit_int_match(cc, "%s"))\n\t\treturn(0);\n\n' % nm)

	fc.write('\tif (clikit_int_eol(cc)) {\n')
	fc.write('\t\tretval = clikit_int_stdinstance(cc, recurse_%d,\n' % nr)
	fc.write('\t\t    \"%s\", \"%s\");\n' % (s,kv['desc']))
	fc.write('\t\tif (retval)\n\t\t\treturn (retval);\n\n')
	fc.write('\t}\n')

	n = 0
	for i in tal:
		fc.write('\tif (%s)\n' % i.conv("cc", "&ivs.arg_%d" % n))
		fc.write('\t\treturn(-1);\n\n')
		n += 1

	fc.write("\tivs.instance.ptr = 0;\n")
	fc.write("\tclikit_int_findinstance(cc, &ivs,")
	fc.write(" recurse_%d, compare_%d);\n" % (nr, nr))
	fc.write("\tif (ivs.instance.ptr == 0 &&\n")
	fc.write("\t    %s(cc" % kv['func'])
	n = 0
	for i in tal:
		fc.write(", ivs.arg_%d" % n)
		n += 1
	fc.write(", &ivs.instance.ptr))\n")
	fc.write("\t\treturn (-1);\n")
	fc.write("\tassert(ivs.instance.ptr != 0);\n")
	# XXX: look for existing instance 
	fc.write("\tclikit_int_addinstance(cc, &ivs,")
	fc.write("\t recurse_%d, sizeof ivs);\n\n" % nr)

	fc.write("\treturn (recurse_%d(cc));\n" % nr)
	fc.write("}\n");

	return kv['name']


def parse(fname, fc, fh):
	fi = open(fname, "r")
	pt = fi.read()
	fi.close()
	tl = shlex.split(pt, "#")
	children = list()
	while len(tl):
		i = tl[0]
		if i == "LEAF":
			children.append(parse_leaf(tl, fc, fh))
		elif i == "INSTANCE":
			children.append(parse_instance(tl, fc, fh))
		else:
			syntax("Unknown '%s' at top" % tl[0])

	if len(children) == 0:
		return

	fh.write("/* At top BRANCH */\n")
	fc.write("\n/* At top BRANCH */\n")

	fh.write("int clikit_match(struct clikit_context *);\n")

	fc.write("int\nclikit_match(struct clikit_context *cc)\n")
	fc.write("{\n")
	fc.write("\tint retval;\n")
	fc.write("\n")
	s = ""
	for i in children:
		print(i)
		fc.write("\t" + s)
		fc.write("if ((retval = %s(cc)) != 0) /*lint !e838*/\n" % i)
		fc.write("\t\t;\n")
		s = "else "
	fc.write("\telse\n")
	fc.write("\t\tretval = 0;\n")
	fc.write("\treturn (retval);\n")
	fc.write("}\n")


#######################################################################
#

def do_tree(argv):
	print("DO_TREE", argv)
	if len(argv) != 1:
		usage("XXX: options not yet implemented")
	fname = os.path.splitext(argv[0])

	fc = open(fname[0] + ".c", "w")
	do_copyright(fc)

	fc.write('#include <assert.h>\n')
	fc.write('#include <string.h>\n')
	fc.write('#define CLIKIT_INTERNAL\n')
	fc.write('#include "clikit.h"\n')
	fc.write('#include "%s.h"\n' % fname[0])

	fh = open(fname[0] + ".h", "w")
	do_copyright(fh)

	parse(argv[0], fc, fh)
	print(fname)
	fc.close()
	fh.close()

#######################################################################
#######################################################################
#

if __name__ == "__main__":
	if len(sys.argv) < 2:
		usage("Need at least one argument")
	elif sys.argv[1] == "--code":
		do_code(sys.argv [2:])
	elif sys.argv[1] == "--tree":
		do_tree(sys.argv [2:])
	else:
		usage("Argument error")
