Sure, here is a simple example of an Abaqus Python script to create a 3D part, material, section, and assembly. This script also assigns the material to the part and creates a step.

```python
# Importing Abaqus modules
from abaqus import *
from abaqusConstants import *

# Creating a new model database
myModel = mdb.Model(name='MyModel')

# Creating a new sketch for the base feature of the part
mySketch = myModel.ConstrainedSketch(name='mySketch', sheetSize=200.0)
mySketch.rectangle(point1=(-100.0, -100.0), point2=(100.0, 100.0))

# Creating a part
myPart = myModel.Part(name='MyPart', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPart.BaseSolidExtrude(sketch=mySketch, depth=200.0)

# Creating a material
myMaterial = myModel.Material(name='MyMaterial')
elasticProperties = (210000.0, 0.3)  # Young's modulus and Poisson's ratio
myMaterial.Elastic(table=(elasticProperties, ))

# Creating a section and assigning it to the part
mySection = myModel.HomogeneousSolidSection(name='MySection', material='MyMaterial', thickness=None)
region = (myPart.cells,)
myPart.SectionAssignment(region=region, sectionName='MySection')

# Creating an assembly
myAssembly = myModel.rootAssembly
myInstance = myAssembly.Instance(name='MyInstance', part=myPart, dependent=ON)

# Creating a step
myModel.StaticStep(name='MyStep', previous='Initial', timePeriod=1.0)
```

Please note that this script is a very basic example and does not include any boundary conditions, loads, mesh, job, etc. You would need to add these to make it a complete model. Also, you need to adjust the parameters according to your needs.