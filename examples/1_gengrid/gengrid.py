#!/usr/bin/env python3
import numpy as np
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-N", type=int, help="number of elements", required=True)
parser.add_argument("-L", type=float, help="left endpoint", required=True)
parser.add_argument("-R", type=float, help="right endpoint", required=True)
parser.add_argument("-MESHTYPE", type=str, choices = ["uniform", "rand","perturb", "power", "paper", "bdry1", "bdry2", "bdry3"], required=True, help="mesh type")
parser.add_argument("-MERGETYPE", type=str, choices = ["LRP", "LRNP", "LP", "RP"], help="LRP = merge to left and right. LRNP = left, right, nonperiodic LP = left periodic. RP = right periodic", required=True)
parser.add_argument("-LOAD", type = str, help="load a grid", default = "null")

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()

num_elem = args.N
left = args.L
right = args.R
mesh_type = args.MESHTYPE
merge_type = args.MERGETYPE
loadgridname = args.LOAD

if mesh_type == "uniform":
    dx = (right-left)/num_elem
    x = np.linspace(left, right, num_elem+1)
elif mesh_type == "rand": # grid points satisfy a uniform distribution
    temp = np.random.rand(num_elem+1)
    dx = (right-left)/num_elem
    temp[0] = 0
    x = np.cumsum(temp)
    x = left + (right-left) * x / x[-1]
elif mesh_type == "perturb":
    temp = np.linspace(0,1, num_elem+1)
    var = 1.
    perturb =  (np.random.rand(num_elem+1)-0.5)*2 * var /num_elem
    temp = temp + perturb
    temp = np.random.rand(num_elem+1)
    dx = (right-left)/num_elem
    temp[0] = 0
    x = np.cumsum(temp)
    x = left + (right-left) * x / x[-1]
elif mesh_type == "power": # grid points satisfy a power law distribution
    a = 0.25
    temp = np.random.power(a, num_elem + 1)
    dx = (right-left)/num_elem
    temp[0] = 0
    x = np.cumsum(temp)
    x = left + (right-left) * x / x[-1]
elif mesh_type == "paper":
    N = num_elem
    num_elem = 2*N + 1 + 2
    alpha = 1e-5 # volume fraction
    dx = (right-left) / (2*N + 1 + alpha * 2)
    reg = np.arange(N+1) * dx
    irreg = np.array( [-0.5 * dx, 0.5 * dx] )
    x = np.hstack( (reg + left, irreg, (alpha + 0.5) * dx + reg) )
elif mesh_type == "bdry1":
    alpha = 1e-5 # volume fraction
    dx = (right - left) / (num_elem-1 + alpha)
    reg = np.arange(num_elem) * dx + alpha*dx
    x = np.hstack( (np.array([0]), reg) ) + left
elif mesh_type == "bdry2":
    alpha = 1e-5 # volume fraction
    dx = (right - left) / (num_elem-2 + 2*alpha)
    reg = np.arange(num_elem-1) * dx + alpha*dx
    x = np.hstack( (np.array([left]), reg+left, np.array([right]) ) ) 
elif mesh_type == "bdry3":
    N = num_elem
    num_elem = 2*N + 1 + 3
    alpha = 1e-5 # volume fraction
    dx = (right-left) / (2*N + 1 + alpha * 3)
    reg1 = np.arange(N) * dx + left + dx * alpha
    irreg = np.array( [0, dx, dx*(1+alpha), dx*(2+alpha), dx*(2 + 2*alpha)] ) + reg1[-1]+dx
    reg2 = np.arange(N-1) * dx + irreg[-1] + dx 
    x = np.hstack( ( np.array([left]), reg1 , irreg, reg2) )
elif mesh_type == "load":
    
    x = np.loadtxt(loadgridname + ".dat")
    with open(loadgridname + ".mdat", 'r') as file:
        indata = file.read().replace('\n', ' ').split()
    dx = float(indata[0])
    merge_type = str(indata[1])
    #TOL = float(indata[2])
    grid_type = str(indata[3])
    num_elem = x.size-1



h = x[1:] - x[:-1]
print("Minimum volume fraction: " , np.min(h/dx) )
#print(h/dx)



print("\n###### MERGING META DATA ######\n")
print("min volume fraction %.16e" % np.min(h/dx) )
if merge_type == "LRNP":
    print("merging type = left and right merging (not periodic)")
elif merge_type == "LRP":
    print("merging type = left and right merging (periodic)")
elif merge_type == "LP":
    print("merging type = left merging (periodic)")
elif merge_type == "RP":
    print("merging type = right merging (periodic)")
else:
    print("merging type not recognized...\n")
    quit()






TOL = dx/2.
print("merging tolerance %lf\n" % (TOL/dx) )
print("###### ----------------- #######\n\n")




m = np.zeros(num_elem)
M = np.zeros(num_elem)
overlaps = np.ones(num_elem)
for elem in range(num_elem):
    left_length = 0
    right_length = 0

    m[elem] = elem
    M[elem] = elem
    
    if h[elem] + 1e-10 >= dx:
        continue


    if merge_type == "LRNP": # merge to left and right (nonperiodic)
        curr = elem-1
        while left_length < TOL and curr > -1:
            left_length = left_length + h[curr]
            m[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = curr - 1
        
        curr = elem+1
        while right_length < TOL and curr < num_elem:
            right_length = right_length + h[curr]
            M[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = curr + 1

        if left_length < TOL:
            curr = int(M[elem]+1)
            while right_length < TOL and curr < num_elem:
                right_length = right_length + h[curr]
                M[elem] = curr
                overlaps[curr] = overlaps[curr] + 1
                curr = curr + 1
        
        if right_length < TOL:
            curr = int(m[elem]-1)
            while left_length < TOL and curr > -1:
                left_length = left_length + h[curr]
                m[elem] = curr
                overlaps[curr] = overlaps[curr] + 1
                curr = curr - 1

    elif merge_type == "LRP": # merge to left and right (periodic)
        curr = (elem-1)%num_elem
        while left_length < TOL:
            left_length = left_length + h[curr]
            m[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = (curr - 1)%num_elem
        
        curr = (elem+1)%num_elem
        while right_length < TOL:
            right_length = right_length + h[curr]
            M[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = (curr + 1)%num_elem
    elif merge_type == "LP": # merge to left (periodic)
        curr = (elem-1)%num_elem
        while left_length < TOL:
            left_length = left_length + h[curr]
            m[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = (curr - 1)%num_elem

    elif merge_type == "RP": # merge to right (periodic)
        curr = (elem+1)%num_elem
        while right_length < TOL:
            right_length = right_length + h[curr]
            M[elem] = curr
            overlaps[curr] = overlaps[curr] + 1
            curr = (curr + 1)%num_elem
       





f=open("grid_"+str(num_elem)+".mdat", 'w')
f.write(str(dx)+"\n")
f.write(str(merge_type)+"\n")
f.write(str(TOL)+"\n")
f.write(str(mesh_type)+"\n")
f.close()
np.savetxt("grid_"+str(num_elem)+".dat", x)

pdata = np.hstack( (m.reshape( (-1,1) ), M.reshape( (-1,1) ), overlaps.reshape( (-1,1) ) )  ).astype(int)
np.savetxt("grid_"+str(num_elem)+".pdat", pdata, fmt="%i")


