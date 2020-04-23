# LICENSE
# 
# _This file is Copyright 2018 by the Image Processing and Analysis Group (BioImage Suite Team). Dept. of Radiology & Biomedical Imaging, Yale School of Medicine._
# 
# BioImage Suite Web is licensed under the Apache License, Version 2.0 (the "License");
# 
# - you may not use this software except in compliance with the License.
# - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
# 
# __Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.__
# 
# ENDLICENSE

import os
import sys
import numpy as np
import unittest
import tempfile
import json
import math

np.set_printoptions(precision=3)
np.set_printoptions(suppress=True)

my_path=os.path.dirname(os.path.realpath(__file__));
sys.path.insert(0,os.path.abspath(my_path+'/../'));
sys.path.insert(0,os.path.abspath(my_path+'/../biswebpython/modules'));

from biswebpython.core.bis_objects import *
import biswebpython.core.bis_baseutils as bis_baseutils;

libbis=bis_baseutils.getDynamicLibraryWrapper();


fname=my_path+'/../test/testdata/pointlocator/brain.json';
file1=open(fname); text1=file1.read(); brain=json.loads(text1);
arr=np.asarray(brain['points'],dtype=np.float32);
print(arr.shape);
l=arr.shape[0];
rows=int(l/3);
cols=3
points=np.reshape(arr,[ rows,cols ]);

m_points=np.ones([rows,cols+1],dtype=np.float32);
print('Size=',points.shape);
print('Size=',m_points.shape);
m_points[:,0:3]=points[:,0:3]

print('____________________________________________________');
print('Num points= ',rows, ' file=',fname);
print("Points 0 & 2 = ",points[0,:], points[2,:])
print("MPoints 0 & 2 = ",m_points[0,:], m_points[2,:])

print('____________________________________________________');


matrix_list = [
    [ [  0.9400000000000001,  0.342,  0 , -21.511 ],
      [  -0.342,  0.9400000000000001,  0,  37.295 ],
      [  0 , 0,  1,  0 ],
      [  0 , 0,  0,  1 ]
    ],
    [ [  1.034,  0.376,  0,  -33.662 ],
      [  -0.376,  1.034,  0,  30.225 ],
      [  0 , 0,  1.1,  -9 ],
      [  0  ,0,  0,  1 ]
    ],
    [ [  0.9380000000000001,  0.38,  0,  -25.44 ],
      [  -0.34600000000000003,  1.032,  0,  27.6 ],
      [  0,  0,  1,  0 ],
      [  0,  0,  0,  1 ]
    ]
]

matrices= [ np.zeros([4,4],dtype=np.float32),
            np.zeros([4,4],dtype=np.float32),
            np.zeros([4,4],dtype=np.float32) ];

for i in range(0,3):
    for row in range(0,4):
        for col in range(0,4):
            matrices[i][row][col]=matrix_list[i][row][col];
    print('Matrix ',i+1,'=',matrices[i]);
        
print('____________________________________________________');

t_points=np.transpose(m_points);


class TestPointLocator(unittest.TestCase):

    def test_fit(self):

        passed=0;
        tested=0;
        numtests=3

        for i in range(0,numtests):

            print('Matrices=',matrices[i].shape,t_points.shape);
            
            warped=np.transpose(np.matmul(matrices[i],t_points))[:,0:3]

            print('In points=', points[0][:], points[4][:]);
            print('In points=', warped[0][:], warped[4][:]);

            out=libbis.computeLandmarkTransformWASM(points,warped,
                                                    { 'mode' : i },0);

            print('Input=\n',matrices[i]);
            print('Output=\n',out);
            print('Difference=\n',abs(matrices[i]-out))
            
            dl=out.flatten()-matrices[i].flatten();
            diff=max(np.amax(dl),-np.amin(dl));
            print('Difference',diff);
            tested+=1
            if (diff<0.1):
                print('_____ P A S S E D ____\n');
                passed=passed+1;
            else:
                print('_____ F A I L E D ____\n');
                
            
            print('____________________________________________________');


        self.assertEqual(passed,tested);
        