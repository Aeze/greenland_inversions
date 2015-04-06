


def generate_sif_file(glacier_name,
                      file_name = None,
                      regularization = 1.0e10,
                      max_iterations = 50):
    """
    Generate an Elmer solver input file (SIF) with the specified parameters.

    Parameters:
    ==========
    glacier_name:   glacier of interest; "helheim", "jakobshavn" or "kangerd"
    file_name:      where to write the output .sif file
    regularization: value of the Tikhonov regularization parameter dictating the
                    degree of smoothing of the solution in order to avoid over-
                    fitting bad input data
    max_iterations: number of iterations to use in the optimization procedure

    Returns: none
    """

    if not glacier_name in ["jakobshavn", "helheim", "kangerd"]:
        raise ValueError("Glacier name must be either jakobshavn, helheim or kangerd.")

    if file_name is None:
        file_name = "elmer/Robin_Beta_" + glacier_name.title() + ".sif"


    text = """
check keywords warn

! name of the run used for the outputs
$name="Robin_Beta"
\n
! Regularization parameter
$Lambda={0}

!some constants
$yearinsec = 365.25*24*60*60
$rhoi = 917.0/(1.0e6*yearinsec^2)  ! MPa - a - m
$gravity = -9.81*yearinsec^2


Header
  Mesh DB "elmer" "{1}3d"
End


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Simulation
  Coordinate System  = Cartesian 3D
  Simulation Type = Steady State

  Output Intervals = 1

  Steady State Max Iterations = {2}
  Steady State Min Iterations = 1

  Output File = "Test_$name".result"
  Post File = "Test_$name".ep"

  Initialize Dirichlet Conditions = Logical False

  max output level = 3
End
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

! Main ice body
Body 1
  Equation = 1
  Body Force = 1
  Material = 1
  Initial Condition = 1
End

! lower surface
Body 2
  Equation = 2
  Body Force = 1
  Material = 1
  Initial Condition = 1
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Initial Condition 1
  MuS = Variable coordinate 1
      Real procedure "lib/Init.so" "muIni"

! initial guess for (square root) slip coeff.
  Beta = Variable Coordinate 1
      Real procedure "lib/Init.so" "betaIni"

  Pressure = Real 0.0
  Velocity 1 = Real 0.0
  Velocity 2 = Real 0.0
  Velocity 3 = Real 0.0

  VeloD 1 = Real 0.0
  VeloD 2 = Real 0.0
  VeloD 3 = Real 0.0
  VeloD 4 = Real 0.0

! Surface velocities (data)
  Vsurfini 1 = Variable Coordinate 1
     Real procedure "lib/Init.so" "USIni"
  Vsurfini 2 = Variable Coordinate 1
     Real procedure "lib/Init.so" "VSIni"
End


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Body Force 1
  Flow BodyForce 1 = Real 0.0
  Flow BodyForce 2 = Real 0.0
  Flow BodyForce 3 = Real $gravity
End


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! ice material properties in MPa - m - a system
Material 1
  Density = Real $rhoi
  Viscosity Model = String "power law"

  Viscosity = Equals MuS

  Viscosity Exponent = Real $1.0e00/3.0e00
  Critical Shear Rate = Real 1.0e-10
End

!!!! Navier-Stokes Solution
Solver 1
  Equation = "Navier-Stokes"

  Stabilize = logical True
  flow model = Stokes

  Linear System Solver = Direct
  Linear System Direct Method =  mumps
  mumps percentage increase working space = integer 60
  !Linear System Solver = Iterative
  ! Linear System Iterative Method = GMRES
  ! Linear System GMRES Restart = 100
  ! Linear System Preconditioning= ILU2
  ! Linear System Convergence Tolerance= 1.0e-08
  ! Linear System Max Iterations = 1000

!
  Nonlinear System Max Iterations = Integer 100
  Nonlinear System Convergence Tolerance  = Real 1.0e-7
  Nonlinear System Newton After Iterations = Integer 10
  Nonlinear System Newton After Tolerance = Real 1.0e-03
  Nonlinear System Relaxation Factor = Real 1.0

  Nonlinear System Reset Newton = Logical True

  Steady State Convergence Tolerance = Real 1.0e-12

! Define  some usefull Variables
  Exported Variable 1 = MuS
  Exported Variable 1 DOFS = 1

! square root of the slip coef
  Exported Variable 2 = Beta
  Exported Variable 2 DOFS = Integer 1
! derivative of the cost fn wr to beta
  Exported Variable 3 = DJDBeta
  Exported Variable 3 DOFS = Integer 1
! value of the cost function
  Exported Variable 4 = CostValue
  Exported Variable 4 DOFS = Integer 1

  Exported Variable 5 = VsurfIni
  Exported Variable 5 DOFS = Integer 2

End

!!!! Navier-Stokes = Dirichlet Problem
Solver 2
  Equation = "NS-Dirichlet"

  Variable = VeloD
  Variable Dofs = 4

  procedure = "FlowSolve" "FlowSolver"

  Linear System Solver = Direct
  Linear System Direct Method = mumps
  mumps percentage increase working space = integer 60
  !Linear System Solver = Iterative
  ! Linear System Iterative Method = GMRES
  ! Linear System GMRES Restart = 100
  ! Linear System Preconditioning= ILU2
  ! Linear System Convergence Tolerance= 1.0e-08
  ! Linear System Max Iterations = 1000


  Nonlinear System Max Iterations = Integer 100
  Nonlinear System Convergence Tolerance  = Real 1.0e-7
  Nonlinear System Newton After Iterations = Integer 10
  Nonlinear System Newton After Tolerance = Real 1.0e-03
  Nonlinear System Relaxation Factor = Real 1.0

  Nonlinear System Reset Newton = Logical True

  Steady State Convergence Tolerance = Real 1.0e-12
End

!!! Compute Cost function
Solver 3

  Equation = "Cost"

!!  Solver need to be associated => Define dumy variable
  Variable = -nooutput "CostV"
  Variable DOFs = 1

  procedure = "../elmerfem/elmerice/ElmerIceSolvers" "CostSolver_Robin"


  Cost Variable Name = String "CostValue"  ! Name of Cost Variable

  Neumann Solution Name = String "Flow Solution"
  Dirichlet Solution Name = String "VeloD"

  Optimized Variable Name = String "Beta"  ! Name of Beta for Regularization
  Lambda = Real  $Lambda                   ! Regularization Coef

  Cost Filename = File "Cost_$name".dat"   ! save the cost as a function of iterations
end

!!!!!  Compute Derivative of Cost function / Beta
Solver 4
  Equation = "DJDBeta"

!!  Solver need to be associated => Define dumy variable
  Variable = -nooutput "DJDB"
  Variable DOFs = 1

  procedure = "../elmerfem/elmerice/ElmerIceSolvers" "DJDBeta_Robin"

  Neumann Solution Name = String "Flow Solution"
  Dirichlet Solution Name = String "VeloD"
  Optimized Variable Name = String "Beta"  ! Name of Beta variable
  Gradient Variable Name = String "DJDBeta"   ! Name of gradient variable
  PowerFormulation = Logical False
  Beta2Formulation = Logical True        ! SlipCoef define as Beta^2

  Lambda = Real  $Lambda                   ! Regularization Coef
end

!!!!! Optimization procedure
Solver 5
  Equation = "Optimize_m1qn3"

!!  Solver need to be associated => Define dumy variable
  Variable = -nooutput "UB"
  Variable DOFs = 1

  procedure = "../elmerfem/elmerice/ElmerIceSolvers" "Optimize_m1qn3Parallel"

  Cost Variable Name = String "CostValue"
  Optimized Variable Name = String "Beta"
  Gradient Variable Name = String "DJDBeta"
  gradient Norm File = String "GradientNormAdjoint_$name".dat"


! M1QN3 Parameters
  M1QN3 dxmin = Real 1.0e-10
  M1QN3 epsg = Real  1.e-6
  M1QN3 niter = Integer 200
  M1QN3 nsim = Integer 200
  M1QN3 impres = Integer 5
  M1QN3 DIS Mode = Logical False
  M1QN3 df1 = Real 0.5
  M1QN3 normtype = String "dfn"
  M1QN3 OutputFile = File  "M1QN3_$name".out"
  M1QN3 ndz = Integer 20

end

Solver 6
  Equation = "ResultOutput"

  Procedure = File "ResultOutputSolve" "ResultOutputSolver"

  Output File Name  = string "Output_$name""
  Vtu Format = logical true
  Binary Output = True
  Single Precision = True

End


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Equation 1
  Active Solvers (4)= 1 2 3 6
  NS Convect= False
End

Equation 2
 Active Solvers (2)=  4 5
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Boundary Condition 1
  Name = "Side Walls"
  Target Boundaries(2) = 4 6

  Velocity 1 = Variable Coordinate 1
    Real procedure "lib/Init.so" "UWa"
  Velocity 2 = Variable Coordinate 1
    Real procedure "lib/Init.so" "VWa"


  VeloD 1 = Variable Coordinate 1
    Real procedure "lib/Init.so" "UWa"
  VeloD 2 = Variable Coordinate 1
    Real procedure "lib/Init.so" "VWa"

End


Boundary Condition 2
  Name = "Inflow and Outflow"
  Target Boundaries(3) = 3 5 7

! Dirichlet BCs
  Velocity 1 = Variable Coordinate 1
    Real procedure "lib/Init.so" "UWa"
  Velocity 2 = Variable Coordinate 1
    Real procedure "lib/Init.so" "VWa"

!Dirichlet BC => Same Dirichlet
  VeloD 1 = Variable Coordinate 1
    Real procedure "lib/Init.so" "UWa"
  VeloD 2 = Variable Coordinate 1
    Real procedure "lib/Init.so" "VWa"
End


Boundary Condition 3
  !Name= "bed" mandatory to compute regularistaion term of the cost function (int (dbeta/dx) 2)
  Name = "bed"
  Target Boundaries(1) = 1
  !Body Id used to solve

  Body ID = Integer 2

  Save Line = Logical True

  Normal-Tangential Velocity = Logical True
  Normal-Tangential VeloD = Logical True

  Velocity 1 = Real 0.0e0
  VeloD 1 = Real 0.0e0

  Slip Coefficient 2 = Variable Beta
     REAL MATC "tx*tx"

  Slip Coefficient 3 = Variable Beta
     REAL MATC "tx*tx"

End

! Upper Surface
Boundary Condition 4
  !Name= "Surface" mandatory to compute cost function
  Name = "Surface"
  Target Boundaries(1) = 2

  Save Line = Logical True

  ! Dirichlet problem applied observed velocities
  VeloD 1 = Equals  Vsurfini 1
  VeloD 2 = Equals  Vsurfini 2

End

    """.format(regularization, glacier_name, max_iterations)

    output_file = open(file_name, "w")
    output_file.write(text)
