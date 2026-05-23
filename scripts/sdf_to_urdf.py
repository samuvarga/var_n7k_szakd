#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def find_text(elem, tag):
    child = elem.find(tag)
    return child.text.strip() if child is not None and child.text else None

def main(sdf_path, out_path):
    tree = ET.parse(sdf_path)
    root = tree.getroot()
    model = root.find('model')
    if model is None:
        print('No <model> found in SDF')
        return 1
    robot_name = model.attrib.get('name','robot')
    urdf = ET.Element('robot', attrib={'name':robot_name})

    # links
    for link in model.findall('link'):
        name = link.attrib.get('name')
        link_el = ET.SubElement(urdf, 'link', attrib={'name': name})
        visual = link.find('visual')
        if visual is not None:
            geom = visual.find('geometry')
            if geom is not None:
                mesh = geom.find('mesh')
                if mesh is not None:
                    uri = find_text(mesh, 'uri')
                    if uri:
                        vis = ET.SubElement(link_el, 'visual')
                        geo = ET.SubElement(vis, 'geometry')
                        m = ET.SubElement(geo, 'mesh', attrib={'filename': uri})
                        # optional origin
                        pose = find_text(visual, 'pose')
                        if pose:
                            # URDF uses xyz rpy; SDF pose order is x y z r p y
                            parts = pose.split()
                            if len(parts) >= 6:
                                origin = ET.SubElement(vis, 'origin', attrib={
                                    'xyz': ' '.join(parts[0:3]),
                                    'rpy': ' '.join(parts[3:6])
                                })
    # joints
    for joint in model.findall('joint'):
        jname = joint.attrib.get('name')
        jtype = joint.attrib.get('type','fixed')
        parent = find_text(joint, 'parent')
        child = find_text(joint, 'child')
        if not parent or not child:
            continue
        j = ET.SubElement(urdf, 'joint', attrib={'name': jname, 'type': jtype})
        ET.SubElement(j, 'parent', attrib={'link': parent})
        ET.SubElement(j, 'child', attrib={'link': child})
        axis = joint.find('axis')
        if axis is not None:
            xyz = find_text(axis, 'xyz')
            if xyz:
                ET.SubElement(j, 'axis', attrib={'xyz': xyz})
            limit = axis.find('limit')
            if limit is not None:
                def clean_num(s):
                    if not s:
                        return '0'
                    s = s.strip()
                    if s.startswith('+'):
                        return s[1:]
                    return s
                lower = clean_num(find_text(limit, 'lower'))
                upper = clean_num(find_text(limit, 'upper'))
                effort = clean_num(find_text(limit, 'effort'))
                velocity = clean_num(find_text(limit, 'velocity'))
                l = ET.SubElement(j, 'limit')
                l.set('lower', lower)
                l.set('upper', upper)
                l.set('effort', effort)
                l.set('velocity', velocity)

    # write pretty
    xmlstr = ET.tostring(urdf, encoding='unicode')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write(xmlstr)
    print('Wrote', out_path)
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: sdf_to_urdf.py model.sdf model.urdf')
        sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
