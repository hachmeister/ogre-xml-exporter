### Info Block ####################################################################

bl_info = {
  "name" : "Ogre XML Exporter",
  "author" : "Karsten Hachmeister",
  "blender" : (2,6,3),
  "version" : (0,0,1),
  "location" : "File > Import-Export",
  "description" : "Export Ogre XML mesh format",
  "category" : "Import-Export"
}

### Imports #######################################################################

import os, pprint
from xml.sax.saxutils import XMLGenerator
import bpy, mathutils
from bpy_extras.io_utils import ExportHelper

### SimpleSaxWriter ###############################################################
# borrowed from the blender2ogre project
# http://code.google.com/p/blender2ogre/

class SimpleSaxWriter():
  def __init__(self, output, encoding, top_level_tag, attrs):
    xml_writer = XMLGenerator(output, encoding, True)
    xml_writer.startDocument()
    xml_writer.startElement(top_level_tag, attrs)
    self._xml_writer = xml_writer
    self.top_level_tag = top_level_tag
    self.ident=4
    self._xml_writer.characters('\n')

  def start_tag(self, name, attrs):
    self._xml_writer.characters(" " * self.ident)
    self._xml_writer.startElement(name, attrs)
    self.ident += 4
    self._xml_writer.characters('\n')

  def end_tag(self, name):
    self.ident -= 4
    self._xml_writer.characters(" " * self.ident)
    self._xml_writer.endElement(name)
    self._xml_writer.characters('\n')

  def leaf_tag(self, name, attrs):
    self._xml_writer.characters(" " * self.ident)
    self._xml_writer.startElement(name, attrs)
    self._xml_writer.endElement(name)
    self._xml_writer.characters('\n')

  def close(self):
    self._xml_writer.endElement(self.top_level_tag)
    self._xml_writer.endDocument()

### Data structures ###############################################################

class Mesh:
  def __init__(self):
    self.sharedgeometry = None
    self.submeshes = None
  
class Geometry:
  def __init__(self):
    self.vertexcount = 0
    self.vertexbuffer_list = []
  
class Vertexbuffer:
  def __init__(self):
    self.positions = False
    self.normals = False
    self.colours_diffuse = False
    self.colours_specular = False
    self.vertex_list = {}
  
class Vertex:
  def __init__(self):
    self.position = None
    self.normal = None
    self.colour_diffuse = None
    self.colour_specular = None
    
  def __eq__(self, o):
    if self.position != o.position or self.normal != o.normal:
      return False
    return True
  
class Vector3:
  def __init__(self, x = 0.0, y = 0.0, z = 0.0):
    self.x = x
    self.y = y
    self.z = z
    
  def __eq__(self, o):
    if self.x != o.x or self.y != o.y or self.z != o.z:
      return False
    return True

class Colour:
  def __init__(self, value = ""):
    self.value = value
    
class Submeshes:
  def __init__(self):
    self.submesh_list = []
  
class Submesh:
  def __init__(self):
    self.material = ''
    self.usesharedvertices = True
    self.use32bitindexes = False
    self.faces = None
  
class Faces:
  def __init__(self):
    self.count = 0
    self.face_list = []
  
class Face:
  def __init__(self, v1 = 0, v2 = 0, v3 = 0):
    self.v1 = v1
    self.v2 = v2
    self.v3 = v3  

### Exporter class ################################################################

class ExportOgreXML(bpy.types.Operator, ExportHelper):
  bl_idname = "mesh.xml"
  bl_label = "Ogre XML Exporter"
  bl_options = {'PRESET'}
  filename_ext = ".xml"
  
  def execute(self, context):
    self.path = os.path.split(self.filepath)[0]
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    objects = bpy.context.selected_objects
    for obj in objects:
      if obj.type == 'MESH':
        mesh = self.mesh(obj)
        self.write_mesh(mesh, obj.name)
    
    return {'FINISHED'};
    
  def mesh(self, obj):
    mesh = Mesh()
    mesh.sharedgeometry = Geometry()
    mesh.submeshes = Submeshes()
    
    #obj.data.update(calc_tessface = True)
    obj.data.calc_tessface()
    obj.data.calc_normals()
    
    # collect materials
    materials = []
    for m in obj.data.materials:
      if m:
        submesh = Submesh()
        submesh.material = m.name
        submesh.faces = Faces()
        mesh.submeshes.submesh_list.append(submesh)
        materials.append(m)
        print(m.name)
    
    # UV
    dotextures = False
    uvcache = []
    if obj.data.tessface_uv_textures.active:
      dotextures = True
#      for layer in obj.data.tessface_uv_textures:
#        uvs = []
#        uvcache.append(uvs)
#        for uvface in layer.data:
#          uvs.append((uvface.uv1, uvface.uv2, uvface.uv3, uvface.uv4))

    # create vertexbuffer
    vbuf = Vertexbuffer()
    vbuf.positions = True
    vbuf.normals = True

    # create faces
    for f in obj.data.tessfaces:
      submesh = mesh.submeshes.submesh_list[f.material_index]
      faces = submesh.faces
      
      face = self.add_face(f, f.vertices[0], f.vertices[1], f.vertices[2], obj, vbuf, mesh.sharedgeometry)
      faces.face_list.append(face)
      faces.count += 1
      
      if len(f.vertices) > 3:
        face = self.add_face(f, f.vertices[0], f.vertices[2], f.vertices[3], obj, vbuf, mesh.sharedgeometry)
        faces.face_list.append(face)
        faces.count += 1
    
    mesh.sharedgeometry.vertexbuffer_list.append(vbuf)
      
    return mesh
    
  def add_face(self, face, v1, v2, v3, obj, vertexbuffer, sharedgeometry):
    idx1 = self.add_vertex(obj.data.vertices[v1], face, vertexbuffer, sharedgeometry)
    idx2 = self.add_vertex(obj.data.vertices[v2], face, vertexbuffer, sharedgeometry)
    idx3 = self.add_vertex(obj.data.vertices[v3], face, vertexbuffer, sharedgeometry)
    
    return Face(idx1, idx2, idx3)
    
  def add_vertex(self, vertice, face, vertexbuffer, sharedgeometry):
    vertex = Vertex()
    
    x, y, z = swap(vertice.co)
    vertex.position = Vector3(x, y, z)
    
    if face.use_smooth:
      nx, ny, nz = swap(vertice.normal)
    else:
      nx, ny, nz = swap(face.normal)
    vertex.normal = Vector3(nx, ny, nz)
    
    for idx in vertexbuffer.vertex_list:
      if vertex == vertexbuffer.vertex_list[idx]:
        return idx
    
    idx = len(vertexbuffer.vertex_list)
    vertexbuffer.vertex_list[idx] = vertex
    sharedgeometry.vertexcount += 1
    return idx

  def write_mesh(self, mesh, name):
    out = open(os.path.join(self.path, name + ".mesh.xml"), 'w')
    doc = SimpleSaxWriter(out, 'UTF-8', "mesh", {})
    
    self.write_geometry(doc, mesh.sharedgeometry)
    self.write_submeshes(doc, mesh.submeshes)
    
    doc.close()
    out.close()
    
  def write_geometry(self, doc, geometry):
    doc.start_tag('sharedgeometry', {
      'vertexcount' : val(geometry.vertexcount)
    })
    for vbuf in geometry.vertexbuffer_list:
      self.write_vertexbuffer(doc, vbuf)
    doc.end_tag('sharedgeometry')
    
  def write_vertexbuffer(self, doc, vertexbuffer):
    doc.start_tag('vertexbuffer', {
      'positions' : val(vertexbuffer.positions),
      'normals' : val(vertexbuffer.normals)
    })
    for idx in range(len(vertexbuffer.vertex_list)):
      self.write_vertex(doc, vertexbuffer.vertex_list[idx])
    doc.end_tag('vertexbuffer')
    
  def write_vertex(self, doc, vertex):
    doc.start_tag('vertex', {})
    self.write_position(doc, vertex.position)
    self.write_normal(doc, vertex.normal)
    doc.end_tag('vertex')
    
  def write_position(self, doc, position):
    doc.leaf_tag('position', {
      'x' : val(position.x),
      'y' : val(position.y),
      'z' : val(position.z)
    })
    
  def write_normal(self, doc, normal):
    doc.leaf_tag('normal', {
      'x' : val(normal.x),
      'y' : val(normal.y),
      'z' : val(normal.z)
    })
    
  def write_submeshes(self, doc, submeshes):
    doc.start_tag('submeshes', {})
    for submesh in submeshes.submesh_list:
      self.write_submesh(doc, submesh)
    doc.end_tag('submeshes')
    
  def write_submesh(self, doc, submesh):
    doc.start_tag('submesh', {
      'material' : val(submesh.material),
      'usesharedvertices' : val(submesh.usesharedvertices),
      'use32bitindexes' : val(submesh.use32bitindexes)
    })
    self.write_faces(doc, submesh.faces)
    doc.end_tag('submesh')
    
  def write_faces(self, doc, faces):
    doc.start_tag('faces', {
      'count' : val(faces.count)
    })
    for face in faces.face_list:
      self.write_face(doc, face)
    doc.end_tag('faces')
    
  def write_face(self, doc, face):
    doc.leaf_tag('face', {
      'v1' : val(face.v1),
      'v2' : val(face.v2),
      'v3' : val(face.v3)
    })
    
### Help functions ################################################################

def val(value):
  if isinstance(value, float):
    return '%6.5f' % value
  elif isinstance(value, bool):
    return str(value).lower()
  elif isinstance(value, int):
    return str(value)
  else:
    return value

def swap(vec):
  if len(vec) == 3:
    return mathutils.Vector([vec.x, vec.z, -vec.y])
  elif len(vec) == 4:
    return mathutils.Quaternion([ vec.w, vec.x, vec.z, -vec.y])
    
### Register/Unregister functions #################################################

def menu_func(self, context):
  self.layout.operator(ExportOgreXML.bl_idname, text = "Ogre XML (.xml)")

def register():
  bpy.utils.register_module(__name__)
  bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
  bpy.utils.unregister_module(__name__)
  bpy.types.INFO_MT_file_export.remove(menu_func)

### Main ##########################################################################

if __name__ == "__main__":
  register()
