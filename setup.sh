mount_dir() {
	sudo mkdir $1
	sudo mount --bind /$1 $1
}

mount_dir bin
mount_dir lib
mount_dir lib64
mount_dir usr
