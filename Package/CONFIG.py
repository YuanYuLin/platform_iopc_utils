import ops
import iopc

pkg_path = ""
output_dir = ""
arch = ""
output_platform_dir = ""
src_image_cfg = ""
dao_script = "dao.py"

def set_global(args):
    global pkg_path
    global output_dir
    global arch
    global src_image_cfg
    global output_platform_dir
    global install_platform_dao

    pkg_path = args["pkg_path"]
    output_dir = args["output_path"]
    arch = ops.getEnv("ARCH_ALT")
    output_platform_dir = ops.path_join(iopc.getOutputRootDir(), "platform")

def MAIN_ENV(args):
    set_global(args)

    return False

def MAIN_EXTRACT(args):
    set_global(args)

    ops.mkdir(output_platform_dir)
    ops.copyto(ops.path_join(pkg_path, dao_script), output_platform_dir)

    return True

def MAIN_PATCH(args, patch_group_name):
    set_global(args)
    for patch in iopc.get_patch_list(pkg_path, patch_group_name):
        if iopc.apply_patch(output_dir, patch):
            continue
        else:
            sys.exit(1)

    return True

def MAIN_CONFIGURE(args):
    set_global(args)
    return False

def MAIN_BUILD(args):
    set_global(args)

    return False

def MAIN_INSTALL(args):
    set_global(args)

    return False

def MAIN_CLEAN_BUILD(args):
    set_global(args)
    return False

def MAIN(args):
    set_global(args)

