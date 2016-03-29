import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
# from mpl_toolkits.mplot3d import Axes3D
import math

x, y, z = np.genfromtxt('list', unpack=True, skip_header=0)
# find lots of points on the piecewise linear curve defined by x and y
M = 1000
t = np.linspace(0, len(x), M)
print(t)
# x = np.interp(t, np.arange(len(x)), x)
# y = np.interp(t, np.arange(len(y)), y)
# z = np.interp(t, np.arange(len(z)), z)
# tol = 0.25
# i, idx = 0, [0]
# while i < len(x):
#     total_dist = 0
#     for j in range(i+1, len(x)):
#         total_dist += math.sqrt((x[j]-x[j-1])**2 + (y[j]-y[j-1])**2 + ((z[j]-z[j-1])**2))
#         if total_dist > tol:
#             idx.append(j)
#             break
#     i = j+1
#
# xn = x[idx]
# yn = y[idx]
# zn = z[idx]
# dx=xn[1]-xn[0]
# dy=yn[1]-yn[0]
# dz=zn[1]-zn[0]
# for i in range(0,2):
#    tx=xn[0]-dx
#    ty=yn[0]-dy
#    tz=zn[0]-dz
#    xn=np.insert(xn,0,tx)
#    yn=np.insert(yn,0,ty)
#    zn=np.insert(zn,0,tz)
#
#
# output = open ("path-equi.dat","w")
# fmt = '{0:14.8f}    {1:14.8f}    {2:14.8f}\n'
# for i in range(0,len(xn)):
#    output.write(fmt.format(xn[i],yn[i],zn[i]))
# output2 = open ("path.xyz","w")
# fmt2= 'C  {0:14.8f}    {1:14.8f}    {2:14.8f}\n'
# output2.write(str(len(xn))+"\n")
# output2.write("\n")
# for i in range(0,len(xn)):
#    output2.write(fmt2.format(xn[i],yn[i],zn[i]))


#fig = plt.figure()
#ax = fig.gca(projection='3d')
#ax.plot(xn,yn,zn,label='path')
#ax.legend()
#plt.show()