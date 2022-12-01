#define _GNU_SOURCE
#include <dlfcn.h>
#include <link.h>
#include <stdio.h>
struct link_map static_map;

char self_proc_name[] = "/proc/self/exe";

int dladdr1(const void *addr, Dl_info *info, void **extra_info, int flags) {
	info->dli_fname = self_proc_name;
	info->dli_fbase = NULL;
	info->dli_sname = NULL;
	info->dli_saddr = NULL;


	if (flags == RTLD_DL_LINKMAP) {
		static_map.l_addr = 0;
		*extra_info = (void*) &static_map;
	}
}
