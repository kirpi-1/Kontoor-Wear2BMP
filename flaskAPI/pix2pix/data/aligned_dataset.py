import os.path
import random
import torchvision.transforms as transforms
import torch
from data.base_dataset import BaseDataset
from data.image_folder import make_dataset
from PIL import Image
#begin custom import
import math


class AlignedDataset(BaseDataset):
    @staticmethod
    def modify_commandline_options(parser, is_train):
        return parser

    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot
        self.dir_AB = os.path.join(opt.dataroot, opt.phase)
        self.AB_paths = sorted(make_dataset(self.dir_AB))
        assert(opt.resize_or_crop == 'resize_and_crop')

    def __getitem__(self, index):
        AB_path = self.AB_paths[index]
        AB = Image.open(AB_path).convert('RGB')
        w, h = AB.size
        assert(self.opt.loadSize >= self.opt.fineSize)
        w2 = int(w / 2)
        A = AB.crop((0, 0, w2-1, h)).resize((self.opt.loadSize, self.opt.loadSize), Image.BICUBIC)
        B = AB.crop((w2, 0, w, h)).resize((self.opt.loadSize, self.opt.loadSize), Image.BICUBIC)
        
        #---------------start my transform additions--------            
        if self.opt.random_crop:
            crop_ratio = random.random()*(1.0-self.opt.random_crop_ratio)+self.opt.random_crop_ratio;    
            width,height = A.size;
            crop_width = width*crop_ratio;
            crop_height = height*crop_ratio;            
            #w,h,w2 (width of one image) 
            #pick the center point
            #10 to 40% of height
            #40 to 60% of width
            x = math.floor(random.random()*width*.2+width*.4);
            y = math.floor(random.random()*height*.3+height*.1);
            #i is for width, j for height
            i=x-crop_width/2;
            if i<0:
                i=0;            
            j=y-crop_height/2;
            if j<0:
                j=0;
            width,height = A.size; #PILImage.size sanity check            
            A = transforms.functional.resized_crop(A,j,i,crop_height,crop_width,(height,width))
            height,width = B.size;
            B = transforms.functional.resized_crop(B,j,i,crop_height,crop_width,(height,width))
            #print("randomly cropping");
            
        if not(self.opt.random_rotation==0.0):
            rot = abs(self.opt.random_rotation);
            deg = random.random()*rot*2-rot;
            whiteBackground = Image.new('RGBA',A.size,(255,)*4);
            Atmp = transforms.functional.rotate(A.convert('RGBA'),deg);
            Btmp = transforms.functional.rotate(B.convert('RGBA'),deg);
            A = Image.composite(Atmp,whiteBackground,Atmp);
            B = Image.composite(Btmp,whiteBackground,Btmp);
            #print("randomly rotating");
        #---------------end my transform additions--------    
        
        A = A.convert('RGB');
        B = B.convert('RGB');
        
        
        A = transforms.ToTensor()(A)
        B = transforms.ToTensor()(B)
        w_offset = random.randint(0, max(0, self.opt.loadSize - self.opt.fineSize - 1))
        h_offset = random.randint(0, max(0, self.opt.loadSize - self.opt.fineSize - 1))

        A = A[:, h_offset:h_offset + self.opt.fineSize, w_offset:w_offset + self.opt.fineSize]
        B = B[:, h_offset:h_offset + self.opt.fineSize, w_offset:w_offset + self.opt.fineSize]

        A = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(A)
        B = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(B)        
        
        
        if (not self.opt.no_flip) and random.random() < 0.5:
            idx = [i for i in range(A.size(2) - 1, -1, -1)]
            idx = torch.LongTensor(idx)
            A = A.index_select(2, idx)
            B = B.index_select(2, idx)

        if self.opt.direction == 'BtoA':
            input_nc = self.opt.output_nc
            output_nc = self.opt.input_nc
        else:
            input_nc = self.opt.input_nc
            output_nc = self.opt.output_nc

        if input_nc == 1:  # RGB to gray
            tmp = A[0, ...] * 0.299 + A[1, ...] * 0.587 + A[2, ...] * 0.114
            A = tmp.unsqueeze(0)

        if output_nc == 1:  # RGB to gray
            tmp = B[0, ...] * 0.299 + B[1, ...] * 0.587 + B[2, ...] * 0.114
            B = tmp.unsqueeze(0)

            

        return {'A': A, 'B': B,
                'A_paths': AB_path, 'B_paths': AB_path}

    def __len__(self):
        return len(self.AB_paths)

    def name(self):
        return 'AlignedDataset'
