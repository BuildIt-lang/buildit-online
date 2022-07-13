#include <string.h>
#include <unistd.h>
int open(const char *pathname, int flags) {
	if (strcmp(pathname, "/proc/self/exe") == 0) {
		return dup(254);
	}
	return -1;
}
