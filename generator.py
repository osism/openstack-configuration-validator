#!/usr/bin/env python3

# Based on https://gitlab.com/yaook/operator/-/blob/devel/buildcue.py (Apache License Version 2.0)

import os
from oslo_config import types
import oslo_config.generator
import pathlib
import subprocess  # nosec
import sys
import yaml


def _flatmap(list):
    return [item for innerlist in list for item in innerlist]


def _genoptions(modulename: str):
    ns = CONFIG_NAMESPACES[modulename]
    groups = oslo_config.generator._get_groups(
        oslo_config.generator._list_opts(ns))
    out = {}
    for groupname, group in sorted(groups.items()):
        out[groupname] = _flatmap([x[0][1] for x in group.values(
        ) if x and not isinstance(x, oslo_config.cfg.OptGroup)])
    return out


def _get_cue_type(groupname, optionname, oslotype, multi=False):
    if isinstance(oslotype, types.List):
        return "[...%s]" % _get_cue_type(
            groupname, optionname, oslotype.item_type)
    elif multi:
        # This needs to be before all other types, as it will otherwise never
        # match first
        return "[...%s]" % _get_cue_type(
            groupname, optionname, oslotype)
    elif isinstance(
            oslotype,
            types.String) or isinstance(
            oslotype,
            str.__class__):
        return "string"
    elif isinstance(oslotype, types.Boolean):
        return "bool"
    elif isinstance(oslotype, types.Integer):
        suffix = "int"
        if oslotype.min:
            suffix = "%s & >= %s" % (suffix, oslotype.min)
        if oslotype.max:
            suffix = "%s & <= %s" % (suffix, oslotype.max)
        return suffix
    elif isinstance(oslotype, types.Float):
        suffix = "float"
        if oslotype.min:
            suffix = "%s & >= %s" % (suffix, oslotype.min)
        if oslotype.max:
            suffix = "%s & <= %s" % (suffix, oslotype.max)
        return suffix
    elif isinstance(oslotype, types.HostAddress):
        return "global.#HostAddress"
    elif isinstance(oslotype, types.URI):
        return "global.#URI"
    elif isinstance(oslotype, types.IPAddress):
        return "global.#IPAddress"
    else:
        print(dir(oslotype))
        print(
            "WARNING: Option of type %s unsupported; group: %s; "
            "option: %s; option will be skipped..." %
            (oslotype, groupname, optionname))
        return "_"


def _writefile(modulename: str, options):
    basepath = pathlib.Path(OUTPUT)
    with open(basepath / f"{modulename}.cue", "w") as output:
        output.write("package %s_template\n" % modulename)
        # output.write("import (\"yaook.cloud/global\")\n")
        output.write("_%s_template_conf_spec: {\n" % modulename)
        for groupname, group in sorted(options.items()):
            output.write('\t"%s"?: {\n' % groupname)
            for option in group:
                line = '"%s"' % option.name
#                if not option.default:
                if not option.required:
                    line = "%s?" % line
                line = "%s:\t" % line
                if option.default:
                    if isinstance(option.default, str):
                        line = "%s*\"%s\" | " % (line,
                                                 option.default.replace(
                                                     '\\',
                                                     '\\\\'
                                                 ).replace(
                                                     '"',
                                                     '\\"'))
                    elif isinstance(option.default, bool):
                        line = "%s*%s | " % (line, str(option.default).lower())
                    elif isinstance(option.default, list):
                        quoted = ['"%s"' % x for x in option.default]
                        line = "%s*[%s] | " % (line,
                                               ", ".join(quoted))
                    else:
                        line = "%s*%s | " % (line, option.default)
                suffix = _get_cue_type(groupname,
                                       option.name, option.type, option.multi)
                output.write("\t\t%s%s\n" % (line, suffix))
            output.write("\t}\n")
        output.write("}\n")


def buildcue(modulename: str):
    options = _genoptions(modulename)
    _writefile(modulename, options)


if __name__ == "__main__":
    GENERATOR = os.environ.get("GENERATOR", "/generator.py")
    NAMESPACES = os.environ.get("NAMESPACES", "/namespaces.yml")
    OUTPUT = os.environ.get("OUTPUT", "/output")

    with open(NAMESPACES) as fp:
        CONFIG_NAMESPACES = yaml.safe_load(fp)

    if len(sys.argv) != 2:
        for module in CONFIG_NAMESPACES.keys():
            # This is to work around oslo config that does not expect to have
            # multiple overlaping configs (e.g. glance and nova) in the same
            # python process. Without this the same config key is defined
            # multiple times (from an oslo.config perspecitve)
            subprocess.run([sys.executable, GENERATOR, module])  # nosec
    else:
        print("Generating config for: %s" % sys.argv[1])
        buildcue(sys.argv[1])
