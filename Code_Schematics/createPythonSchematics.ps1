

conda activate ces-mma
$path_code = ".\code_python\enceladus"
$time = get-date -f yyyy-MM-dd:hh:mm
$path_uml = ".\Code_Schematics\codeschematic_UML$(get-date -f yyyy-MM-dd-hh-mm).txt"
py2puml $path_code code_python.enceladus |
    Out-String |
    Set-Content $path_uml
plantUML $path_uml