BEGIN {
	found_buildroot = 0;
}

{
	if (/^BuildRoot: /)
		found_buildroot = 1;

	if (part == "start") {
		print $0;

		if (found_buildroot)
			exit;

	} else if (part == "end") {
		if (found_buildroot && ! /^BuildRoot: /)
			print $0;

	} else {
		exit;
	}
}

