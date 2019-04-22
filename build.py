#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import subprocess
import re
import json
import xml.dom.minidom
import sys
import getopt


class BuildClass(object):


    def __init__(self, provisioning_profile_uuid, certification_name, *, configuration='', teamId=None, scheme=None, quiet=False, output_path = None):
        self.tmpPath = "./.tmp/"
        self.provisioning_profile_uuid = provisioning_profile_uuid
        self.certification_name = certification_name
        self.configuration = configuration
        self.teamId = teamId
        self.scheme = scheme
        self.quiet = quiet
        self.buildPath = './dataBuild'
        self.workspaceFile = None
        self.projectFile = ''
        if output_path:
            self.savePath = output_path
        else:
            self.savePath = './output'
        self.ipaPath = './ipaInfo.plist'


    def build(self):
        self.__prepare()
        cmds = [
            "xcodebuild",
            "build",
            "-scheme", self.scheme,
            "-configuration", self.configuration,
            "-derivedDataPath", self.buildPath,
        ]
        if self.workspaceFile:
            cmds.append('-workspace')
            cmds.append(self.workspaceFile)
        if len(self.provisioning_profile_uuid) > 0:
            cmds.append("PROVISIONING_PROFILE_SPECIFIER=" + self.provisioning_profile_uuid)
        if len(self.certification_name) > 0:
            cmds.append("CODE_SIGN_IDENTITY=" + self.certification_name)
        if self.teamId and len(self.teamId) > 0:
            cmds.append("DEVELOPMENT_TEAM=" + self.teamId)
        if len(self.provisioning_profile_uuid) > 0 or len(self.certification_name) > 0 or (self.teamId and len(self.teamId)):
            cmds.append("CODE_SIGN_STYLE=Manual")
        if self.__execute(cmds) == 0:
            print("Build project success!")


    def clean(self):
        if os.path.exists(self.ipaPath):
            os.remove(self.ipaPath)
        if os.path.exists(self.tmpPath):
            cmds = [
                "rm",
                "-rf",
                self.tmpPath,
            ]
            if self.__execute(cmds) == 0:
                print('Clean temp dir success')
        if os.path.exists(self.buildPath):
            cmds = [
                "rm",
                "-rf",
                self.buildPath,
            ]
            if self.__execute(cmds) == 0:
                print('Clean dirs success')
    

    def archive(self):
        self.__prepare()
        archivePath = self.savePath + '/' + self.scheme + '.xcarchive'
        if os.path.exists(archivePath):
            subprocess.call(['rm', '-rf', archivePath])
        
        
        print('use scheme: %s' % self.scheme)
        print('use configuration: %s' % self.configuration)
        cmds = [
            'xcodebuild',
            'archive',
            "-scheme", self.scheme,
            "-configuration", self.configuration,
            "-derivedDataPath", self.buildPath,
            "-archivePath", archivePath,
        ]
        if self.workspaceFile:
            cmds.append('-workspace')
            cmds.append(self.workspaceFile)
        if len(self.provisioning_profile_uuid) > 0:
            cmds.append("PROVISIONING_PROFILE_SPECIFIER=" + self.provisioning_profile_uuid)
        if len(self.certification_name) > 0:
            cmds.append("CODE_SIGN_IDENTITY=" + self.certification_name)
        if self.teamId:
            cmds.append("DEVELOPMENT_TEAM=" + self.teamId)
        if len(self.provisioning_profile_uuid) > 0 or len(self.certification_name) > 0 or self.teamId:
            cmds.append("CODE_SIGN_STYLE=Manual")
        if self.__execute(cmds) == 0:
            print("Archive project success!")


    def exportArchive(self):
        self.__prepare()
        self.__createPlistFile(self.buildInfo['buildSettings']['PRODUCT_BUNDLE_IDENTIFIER'])
        archivePath = self.savePath + '/' + self.scheme + '.xcarchive'
        exportPath = self.savePath + '/Exported'
        cmds = [
            "xcodebuild",
            "-exportArchive",
            "-archivePath", archivePath,
            "-exportPath", exportPath,
            "-exportOptionsPlist", self.ipaPath,
        ]
        if len(self.provisioning_profile_uuid) > 0:
            cmds.append("PROVISIONING_PROFILE_SPECIFIER=" + self.provisioning_profile_uuid)
        if len(self.certification_name) > 0:
            cmds.append("CODE_SIGN_IDENTITY=" + self.certification_name)
        if self.teamId:
            cmds.append("DEVELOPMENT_TEAM=" + self.teamId)
        if len(self.provisioning_profile_uuid) > 0 or len(self.certification_name) > 0 or self.teamId:
            cmds.append("CODE_SIGN_STYLE=Manual")
        if self.__execute(cmds) == 0:
            print("Export project success!")


    def __prepare(self, path='.'):
        opt = []
        for subpath in os.listdir(path):
           if re.match(r'\S+.xcodeproj', subpath):
                self.projectFile = subpath
                opt.append(subpath)
           elif re.match(r'\S+.xcworkspace', subpath):
                self.workspaceFile = subpath
                opt.append(subpath)
        if len(opt) == 0:
            exit(2)
        if not self.scheme:
            info = self.__getInfo()
            schemeList = info['project']['schemes']
            self.scheme = schemeList[0]
        self.buildInfo = self.__get_build_settings(self.scheme)
        if self.configuration == None or len(self.configuration) == 0:
            self.configuration = self.buildInfo['buildSettings']['CONFIGURATION']


    def __createPlistFile(self, bundleId):
        if self.configuration == 'Release':
            self.method = 'app-store'
        else:
            self.method = 'development'
        ipaInfoDic = {
            "signingCertificate": self.certification_name,
            "provisioningProfiles": {
                bundleId: self.provisioning_profile_uuid
            },
            "method": self.method,
            "compileBitcode": True
        }
        fileExist = os.path.exists(self.ipaPath)
        if fileExist:
            os.remove(self.ipaPath)
        try:
            f = open(self.ipaPath, 'w')
            f.write(json.dumps(ipaInfoDic))
        finally:
            f.close()
            self.__execute_sys([
                'plutil', 
                '-convert', 'xml1',
                self.ipaPath
            ])

    
    def __get_build_settings(self, scheme=None):
        if not os.path.exists(self.tmpPath):
            os.mkdir(self.tmpPath)
        settingsPath = self.tmpPath + 'build_settings.json'
        if os.path.exists(settingsPath):
            jsonStr = self.__readFile(settingsPath)
            obj = json.loads(jsonStr)
            return obj[0]
        else:
            cmds = [
                'xcodebuild',
                '-showBuildSettings',
                '-json'
            ]
            if scheme:
                cmds.append('-scheme')
                cmds.append(scheme)
            jsonStr = subprocess.check_output(cmds).decode('utf-8')
            self.__writeToFile(jsonStr, settingsPath)
            obj = json.loads(jsonStr)
            return obj[0]
        

    
    def __getInfo(self):
        if not os.path.exists(self.tmpPath):
            os.mkdir(self.tmpPath)
        infoPath = self.tmpPath + 'info.json'
        if os.path.exists(infoPath):
            jsonStr = self.__readFile(infoPath)
            obj = json.loads(jsonStr)
            return obj
        else:
            cmds =[
                'xcodebuild',
                '-list',
                "-json"
            ]
            jsonStr = subprocess.check_output(cmds).decode('utf-8')
            self.__writeToFile(jsonStr, infoPath)
            obj = json.loads(jsonStr)
            return obj
        
    def __execute_sys(self, cmds):
        p = subprocess.Popen(cmds)
        v = p.wait()
        if v == 0:
            return 0
        else:
            exit(v)

    def __execute(self, cmds):
        if self.quiet:
            cmds.append('-quiet')
        p = subprocess.Popen(cmds)
        v = p.wait()   
        if v == 0:
            return 0
        else:
            exit(v)
    

    def __writeToFile(self, content, filename):
        with open(filename, 'w') as f:
            f.write(content)
        
    def __readFile(self, filename):
        with open(filename, 'r') as f:
            return f.read()


hText = '''Usage: 
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
'''

def main(argv):
    act = 'build'
    provisioningProfiles = ''
    certificationName = ''
    teamId = ''
    scheme = ''
    configuration = ''
    quiet = False
    output = ''
    try:
        opts, args = getopt.getopt(argv, "hp:C:t:s:c:qvo:", ["help", "provisioning-profile-uuid=", "certification-name=", "team-id=", "scheme=", "configuration=", "quiet", "version", "output="])
        for opt_name, opt_value in opts:
            if opt_name in ('-h', '--help'):
                print(hText)
                exit()
            if opt_name in ('-v', '--version'):
                print('Version 0.1')
                exit()
            if opt_name in ('-p', '--provisioning-profile-uuid'):
                provisioningProfiles = opt_value
            if opt_name in ('-c', '--certification-name'):
                certificationName = opt_value
            if opt_name in ('-t', '--team-id'):
                teamId = opt_value
            if opt_name in ('-s', '--scheme'):
                scheme = opt_value
            if opt_name in ('-C', '--configuration'):
                configuration = opt_value
            if opt_name in ('-q', '--quiet'):
                quiet = True
            if opt_name in ('-o', '--output'):
                output = opt_value
        if len(args) > 1:
            print(hText)
            exit(2)
        elif len(args) == 0:
            act = 'build'
        else :
            act = args[0]
    except getopt.GetoptError:
        print("err")
        sys.exit(2)
    if act in ('build', 'clean', 'archive', 'export'):
        builder = BuildClass(provisioning_profile_uuid=provisioningProfiles, certification_name=certificationName, teamId=teamId, scheme=scheme, configuration=configuration, quiet=quiet, output_path=output)
        if act == 'build':
            builder.build()
        elif act == 'clean':
            builder.clean()
        elif act == 'archive':
            builder.archive()
        elif act == 'export':
            builder.exportArchive()
        else:
            print(hText)
            exit(3)
    else:
        print(hText)
        exit(3)
    

if __name__ == "__main__":
    main(sys.argv[1:])



