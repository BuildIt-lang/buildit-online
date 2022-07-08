#include <seccomp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <asm/prctl.h>
#include <fcntl.h> 

#define ADD_SECCOMP_RULE(ctx, ...)                      \
        do {                                                  \
                if(seccomp_rule_add(ctx, __VA_ARGS__) < 0) {        \
                        fprintf(stderr, "Could not add seccomp rule");             \
                        seccomp_release(ctx);                             \
                        exit(-1);                                         \
                }                                                   \
        } while(0)

static void sig_handler(int signum) {
	fprintf(stderr, "Process tried to do an action it is not allowed with %d - KILLING\n", signum);
	exit(-1);
}

void insert_seccomp_filters(void) {
	signal(SIGSYS, sig_handler);

	static scmp_filter_ctx ctx;
	ctx = seccomp_init(SCMP_ACT_TRAP);
	if(ctx == NULL) {
		fprintf(stderr, "Could not open seccomp context");
		exit(-1);
	}	
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit      ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(tgkill      ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read      ), 0);

	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(brk       ), 0);

	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mmap      ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(munmap      ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execve     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(futex     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(fstat     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(access     ), 0);

	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigreturn     ), 0);
	//ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigprocmask     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(getpid     ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(gettid     ), 0);

	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close    ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(uname    ), 0);
	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(readlink    ), 0);

	ADD_SECCOMP_RULE(ctx, SCMP_ACT_ALLOW, SCMP_SYS(arch_prctl), 1, SCMP_CMP(0, SCMP_CMP_EQ, ARCH_SET_FS));

	if(seccomp_load(ctx) < 0) {
		fprintf(stderr, "Could not load seccomp context\n");
		exit(-1);
	}

}


#define FIXED_FD_SELF (254)


int main(int argc, char * argv[]) {
	if (argc < 2) {
		printf("Usage: %s <executable>\n", argv[0]);
		return -1;
	}
	
	int fd = open(argv[1], O_RDONLY);
	if (fd < 0) {
		printf("Error spawning isolated process while opening fd\n");
		return -1;
	}	
	if (dup2(fd, FIXED_FD_SELF) < 0) {
		printf("Error spawning isolated process while duping fd\n");
		return -1;
	}
	close (fd);
	insert_seccomp_filters();


	char* args[] = {argv[1], NULL};
	char* envs[] = {NULL};
	
	execve(argv[1], args, envs);
	exit(-1);
}
