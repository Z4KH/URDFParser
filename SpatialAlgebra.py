import sympy as sp
import numpy as np
import copy

class Translation:
    def __init__(self, x, y = None, z = None):
        if y == None: # passed in as tuple
            self.y = x[1]
            self.z = x[2]
            self.x = x[0]
        else:
            self.x = x
            self.y = y
            self.z = z
        self.rx = self.skew(self.x,self.y,self.z)
        self.Xmat_sp_fixed = self.xlt(self.rx)

    def skew(self, x, y, z):
        return sp.Matrix([[0,-z,y],[z,0,-x],[-y,x,0]])

    def xlt(self, rx):
        col1 = sp.Matrix.vstack(sp.eye(3), -rx)
        col2 = sp.Matrix.vstack(sp.zeros(3, 3), sp.eye(3))
        return sp.Matrix.hstack(col1, col2)

    def gen_tx_hom(self, x, y, z, inv = False):
        if inv:
            return sp.Matrix([[1,0,0,-x],[0,1,0,-y],[0,0,1,-z],[0,0,0,1]])
        else:
            return sp.Matrix([[1,0,0,x],[0,1,0,y],[0,0,1,z],[0,0,0,1]])

class Rotation:
    def __init__(self, r, p = None, y = None):
        if p == None: # passed in as tuple
            self.p = r[1]
            self.y = r[2]
            self.r = r[0]
        else:
            self.r = r
            self.p = p
            self.y = y

        roll_mat = self.rx(self.r)
        pitch_mat = self.ry(self.p)
        yaw_mat = self.rz(self.y)
        self.E = roll_mat * pitch_mat * yaw_mat
        self.Xmat_sp_fixed = self.rot(self.E)

    def rx(self, theta):
        c = sp.cos(theta)
        s = sp.sin(theta)
        E = sp.Matrix([[1, 0, 0], [0, c, s], [0, -s, c]])
        return E

    def ry(self, theta):
        c = sp.cos(theta)
        s = sp.sin(theta)
        E = sp.Matrix([[c, 0, -s], [0, 1, 0], [s, 0, c]])
        return E

    def rz(self, theta):
        c = sp.cos(theta)
        s = sp.sin(theta)
        E = sp.Matrix([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        return E

    def rot(self, E):
        z = sp.zeros(3, 3)
        col1 = sp.Matrix.vstack(E, z)
        col2 = sp.Matrix.vstack(z, E)
        return sp.Matrix.hstack(col1, col2)

    def rot_hom(self, E):
        left = sp.Matrix.vstack(E,sp.Matrix([[0,0,0]]))
        return sp.Matrix.hstack(left,sp.Matrix([[0],[0],[0],[1]]))

class Origin:
    def __init__(self):
        self.translation = None
        self.rotation = None
        self.Xmat_sp_fixed = None
        self.Xmat_sp_hom_fixed = None

    def set_translation(self, x, y = None, z = None):
        self.translation = Translation(x,y,z)

    def set_rotation(self, r, p = None, y = None):
        self.rotation = Rotation(r,p,y)

    def build_fixed_transform(self):
        if self.translation is None or self.rotation is None:
            print("[!Error] First set the origin translation and rotation!")
        else:
            self.Xmat_sp_fixed =  self.rotation.Xmat_sp_fixed * self.translation.Xmat_sp_fixed
            # now build the homogenous [R | xyz
            #                           0 | 1 ]
            self.Xmat_sp_hom_fixed = copy.deepcopy(self.rotation.rot_hom(self.rotation.E))
            self.Xmat_sp_hom_fixed_inv = copy.deepcopy(self.rotation.rot_hom(self.rotation.E.transpose()))
            self.Xmat_sp_hom_fixed[0,3] = self.translation.x
            self.Xmat_sp_hom_fixed[1,3] = self.translation.y
            self.Xmat_sp_hom_fixed[2,3] = self.translation.z
            self.Xmat_sp_hom_fixed_inv[0,3] = -self.translation.x
            self.Xmat_sp_hom_fixed_inv[1,3] = -self.translation.y
            self.Xmat_sp_hom_fixed_inv[2,3] = -self.translation.z


class Quaternion_Tools:
    def __init__(self):
        pass
        
    def quat_to_rpy(self, q0, q1, q2, q3):
        r = np.atan2(2*q2*q3+2*q0*q1, q3^2-q2^2-q1^2+q0^2)
        p = -np.asin(2*q1*q3-2*q0*q2)
        y = np.atan2(2*q1*q2+2*q0*q3, q1^2+q0^2-q3^2-q2^2)
        return (r,p,y)

    def quat_to_rot_sp(self, q0, q1, q2, q3):
        # GRiD uses a wxyz quaternion, convert to xyzw form for the matrix calculation
        # using https://automaticaddison.com/how-to-convert-a-quaternion-to-a-rotation-matrix/
        temp = q0
        q0 = q1
        q1 = q2
        q2 = q3
        q3 = temp

        total = sp.sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3)
        q0 = q0/total
        q1 = q1/total
        q2 = q2/total
        q3 = q3/total

        q0s = q0*q0
        q1s = q1*q1
        q2s = q2*q2
        q3s = q3*q3
        q01 = q0*q1
        q02 = q0*q2
        q03 = q0*q3
        q12 = q1*q2
        q13 = q1*q3
        q23 = q2*q3

        E = 2 * sp.Matrix([[(q0s + q1s) - 0.5, q12 + q03,         q13 - q02],
        [q12 - q03,         (q0s + q2s) - 0.5, q23 + q01],
        [q13 + q02,         q23 - q01,         (q0s + q3s) - 0.5]])

        return E

    def quat_to_rot_np(self, q0, q1, q2, q3):
        total = np.sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3)
        q0 = q0/total
        q1 = q1/total
        q2 = q2/total
        q3 = q3/total

        q0s = q0*q0
        q1s = q1*q1;
        q2s = q2*q2;
        q3s = q3*q3;
        q01 = q0*q1;
        q02 = q0*q2;
        q03 = q0*q3;
        q12 = q1*q2;
        q13 = q1*q3;
        q23 = q2*q3;

        E = 2 * np.matrix([[q0s + q1s - 0.5, q12 + q03,       q13 - q02],
                           [q12 - q03,       q0s + q2s - 0.5, q23 + q01],
                           [q13 + q02,       q23 - q01,       q0s + q3s - 0.5]])
        return E

    def rpy_to_quat(self, r, p, y):
        pass

