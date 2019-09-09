% LICENSE
% 
% _This file is Copyright 2018 by the Image Processing and Analysis Group (BioImage Suite Team). Dept. of Radiology & Biomedical Imaging, Yale School of Medicine._
% 
% BioImage Suite Web is licensed under the Apache License, Version 2.0 (the "License");
% 
% - you may not use this software except in compliance with the License.
% - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
% 
% __Unless required by applicable law or agreed to in writing, software
% distributed under the License is distributed on an "AS IS" BASIS,
% WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
% See the License for the specific language governing permissions and
% limitations under the License.__
% 
% ENDLICENSE

clear

bispath();
lib=biswrapper();

m=mfilename('fullpath');
[filepath,name,ext] = fileparts(m);
[filepath,name,ext] = fileparts(filepath);
fname1=[ filepath filesep  'test' filesep 'testdata' filesep 'MNI_2mm_resliced.nii.gz'];
fname2=[ filepath filesep  'test' filesep 'testdata' filesep 'newtests' filesep 'goldsmooth2sigma.nii.gz'];
disp(fname1);
disp(fname2);
format long;

param.sigmas=[2.0,2.0,2.0 ];
param.radiusfactor=2.0;
param.inmm='true'
debug=1;

% Load Images
input = load_untouch_nii(fname1,[],[],[],[],[],[]);
disp(input)


gold = load_untouch_nii(fname2,[],[],[],[],[],[]);
disp(gold)

disp('----------------------------------');
disp('Smoothing image');
output = lib.gaussianSmoothImageWASM(input, param, debug);


disp(['Testing fake difference=']);
max(max(max(abs(gold.img-single(input.img)))))


disp(['Testing real difference']);
max(max(max(abs(gold.img-single(output.img)))))


disp('----------------------------------');
disp('Smoothing image 2');
output2 = lib.gaussianSmoothImageWASM(input, param, debug);


disp(['Testing real difference v2']);
max(max(max(abs(gold.img-single(output2.img)))))


disp('----------------------------------');
disp('Smoothing image 2');
param.sigmas=[0.1,0.1,0.1];

output3 = lib.gaussianSmoothImageWASM(input, param, debug);

disp(['Testing real difference 3']);
max(max(max(abs(gold.img-single(output3.img)))))
return;


