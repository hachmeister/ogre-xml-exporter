### Info Block ####################################################################

bl_info = {
  "name" : "Ogre Exporter",
  "author" : "Karsten Hachmeister",
  "blender" : (2,6,3),
  "version" : (0,0,1),
  "location" : "File > Import-Export",
  "description" : "Export Ogre XML mesh format",
  "category" : "Import-Export"
}

### Imports #######################################################################

import os
import bpy
from bpy_extras.io_utils import ExportHelper

### Exporter class ################################################################

class ExportOgreXML(bpy.types.Operator, ExportHelper):
  bl_idname = "mesh.xml";
  bl_label = "Ogre XML Exporter";
  bl_options = {'PRESET'};
  filename_ext = ".xml";
  
  def execute(self, context):
    self.out = open(self.filepath, 'w');
    
    print('Export path:', self.filepath)
    prefix = self.filepath.split('.')[0]
    path = os.path.split(self.filepath)[0]
    print('Path:', path)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    objects = bpy.context.selected_objects
    
    for obj in objects:
      if obj.type == 'MESH':
        self.export_object(obj)
    
    self.out.close()
    return {'FINISHED'};
    
  def export_object(self, obj):
    obj.data.update(calc_tessface = True)
    self.out.write("Object: " + obj.name + ", Data: " + obj.data.name + "\n")
    self.out.write("  Vertices: " + str(len(obj.data.vertices)) + ", Faces: " + str(len(obj.data.tessfaces)) + "\n")
    vertices = obj.data.vertices
    faces = obj.data.tessfaces
    for face in faces:
      self.out.write(str(vertices[face.vertices[0]]) + ";" + str(vertices[face.vertices[1]]) + ";" + str(vertices[face.vertices[2]]))
      if len(face.vertices) > 3:
        self.out.write(str(vertices[face.vertices[0]]) + ";" + str(vertices[face.vertices[2]]) + ";" + str(vertices[face.vertices[3]]))

### Register/Unregister functions #################################################

def menu_func(self, context):
  self.layout.operator(ExportOgreXML.bl_idname, text = "Ogre XML (.xml)");

def register():
  bpy.utils.register_module(__name__);
  bpy.types.INFO_MT_file_export.append(menu_func);

def unregister():
  bpy.utils.unregister_module(__name__);
  bpy.types.INFO_MT_file_export.remove(menu_func);

###################################################################################

if __name__ == "__main__":
  register()