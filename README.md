# xcodebuild_python
An automatically building python script


# Usage: 

	./build.py [[-h]|[--help]] [[-v]|[--version]] [[-q][--quiet]] [[-a <actionname>]|[-action]] [[-p provisionprofileuuid]|[--provisioning-profile-uuid provisionprofileuuid]] [[-c certname]|[--certification-name certname]] [[-t teamid]|[--team-id teamid]] [[-s scheme]|[--scheme scheme]] [[-C configuration]|[--configuration configuration]] [[-o outputpath]|[--output outputpath]] <build|clean|archive|export>

	Options:
    -h --help                               : this help
    -v --version                            : show version
    -q --quiet                              : do not print any output except for warnings and errors
    -p --provisioning-profile-uuid uuid     : provisioning profile uuid
    -c --certification-name cert name       : certification name
    -t --team-id team id                    : developer's team ID
    -s --scheme scheme                      : build sheme of the project
    -C --configuration configuration        : build configuration of the project
    -o --output path                        : export path for project
