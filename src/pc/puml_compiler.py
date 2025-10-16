from typing import cast
from json import dumps

from pc.parser.parser import Parser
from pc.postparse.ppvisitors import PostParse, GenData
from pc.errorlog.error import StackedErrorContext, Severity, CompilerResults
from pc.codegen.graphml.objs2graphml import graphml
from pc.astree.ast import AstNode


def puml_compiler(
    src_file: str, ec: StackedErrorContext, to_json: bool
) -> CompilerResults:
    err = CompilerResults(1, "")
    with open(src_file, "rt", encoding="utf8") as fsrc:
        text = fsrc.read()
    p = Parser(src_file, ec)
    r = p.parse(text)
    if ec.max_severity >= Severity.ERROR:
        return err
    PostParse(cast(AstNode, r), ec)
    if ec.max_severity >= Severity.ERROR:
        return err
    objects = GenData(cast(AstNode, r), ec).get_data()
    if to_json:
        data = dumps(objects, sort_keys=True, indent=1)
    else:
        data = graphml(objects, ec)
    # if ec.max_severity >= Severity.ERROR: #should never happen
    #    return err #pragma: no cover
    return CompilerResults(int(ec.max_severity >= Severity.ERROR), data)
