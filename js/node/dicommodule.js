/*  LICENSE

    _This file is Copyright 2018 by the Image Processing and Analysis Group (BioImage Suite Team). Dept. of Radiology & Biomedical Imaging, Yale School of Medicine._

    BioImage Suite Web is licensed under the Apache License, Version 2.0 (the "License");

    - you may not use this software except in compliance with the License.
    - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

    __Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.__

    ENDLICENSE */

    'use strict';

    const BaseModule = require('basemodule.js');
    const baseutils=require("baseutils");

    const exec = require('child_process').exec;
    
    class InfoModule extends BaseModule {
      constructor() {
        super();
        this.name = 'Info';
      }
        
        createDescription() {
            
            return {
                "name": "Info",
                "description": "This module converts raw DICOM data into NIFTI form using dcm2niix, then formats it to BIDS specifications",
                "author": "Zach Saltzman",
                "version": "1.0",
                "inputs": [],
                "outputs": [
                    {
                        'type' : 'text',
                        'name' : 'Results',
                        'description': 'log file',
                        'varname': 'logoutput',
                        'required': false,
                        'extension': '.bistext'
                    },
                ],
                "buttonName": "Execute",
                "shortname" : "info",
                "params": [
                    {
                        "name": "Input Directory",
                        "description": "Input directory for the DICOM conversion",
                        "advanced": true,
                        "type": "string",
                        "varname": "indir"
                    },
                    baseutils.getDebugParam()
                ]
            };
        }
    
    
        directInvokeAlgorithm(vals) {
    
            console.log('oooo invoking: dicommodule with vals', JSON.stringify(vals));
            
            let errorfn=( (msg, e = 'No available error message') => {
                console.log('error in dicom conversion', msg, e);
                this.sendCommand(socket,'dicomConversionError', { 
                    'output' : msg,
                    'id' : id });
                return false;
            });
            
            let id=opts.id;
            let indir=opts.indir || '';
    
            if (path.sep==='\\') {
                indir=util.filenameUnixToWindows(indir);
            }
            

            exec('which asdf', (err) => {
                if (err) { console.log('Error: cannot find dcm2niix'); }
                
            });
            
            if (!this.validateFilename(indir)) {
                return errorfn(indir+' is not valid');
            }
    
            //TODO: Make this generic
            let dicomtmpdir=path.join(this.opts.tempDirectory,'dicom_' + Date.now());
            let outdir = dicomtmpdir + '/derived';
            try {
                fs.mkdirSync(dicomtmpdir);
                fs.mkdirSync(outdir);
            } catch (e) {
                console.log('An error occured while making DICOM directories', e);
                return false;
            }
            
            let done= (status,code) => {
                if (status===false) {
                    return errorfn('dcm2nii failed'+code);
                }
                
                this.sendCommand(socket,'dicomConversionDone', { 
                    'output' : outdir,
                    'id' : id });
                return;
            };
    
            let listen= (message) => {
                this.sendCommand(socket,'dicomConversionProgress', message);
            };
    
            console.log('indir', indir, 'outdir', outdir);
            let cmd = this.opts.dcm2nii + ' -z y ' + ' -o ' + outdir + ' -ba y -c bisweb ' + indir;
            biscmdline.executeCommand(cmd,__dirname,done,listen);
            return;

            
            return Promise.resolve(msg);
        }
    }
    
    module.exports = InfoModule;
    