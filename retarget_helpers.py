# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy


def delete_blender_obj(obj):
	for collection in list(obj.users_collection):
		collection.objects.unlink(obj)
	if obj.users == 0:
		bpy.data.objects.remove(obj)
	del obj


def clear_animation_action_on_armature(armature):
	armature.animation_data.action = None
	

def delete_all_nla_tracks_on_armature(armature):
	armature.animation_data.nla_tracks

	track_list = []
	for track in armature.animation_data.nla_tracks:
		track_list.append(track)
		
	for track in track_list:
		armature.animation_data.nla_tracks.remove(track)


def push_armature_action_to_new_nla_strip(armature, frame_from, track_name, strip_name):
	if armature.animation_data is not None:
		action = armature.animation_data.action
		if action is not None:
			track = armature.animation_data.nla_tracks.new()
			track.name = track_name
				  
			strip = track.strips.new(strip_name, 1, action)
			strip.name = strip_name
			track.lock = True
			track.mute = True
			
			clear_animation_action_on_armature(armature)
			

def push_fbx_animation_to_target_rig_nla_track(fbx_abs_path, anim_name):
	scene = bpy.context.scene
	
	bpy.ops.import_scene.fbx(
		filepath = fbx_abs_path, 
		automatic_bone_orientation = True,
		ignore_leaf_bones = True, 
		anim_offset = 0)
		
	# Update ARP's source rig.
	scene.source_rig = bpy.context.active_object.name
	
	# Clear current action on target armature.
	target_rig_name = scene.target_rig
	target_rig = scene.objects[target_rig_name]

	target_rig.animation_data.action = None

	###
	### Reset the base pose on source armature.
	###

	# Press Redefine Rest Pose equivalent
	bpy.ops.arp.redefine_rest_pose(rest_pose='REST', preserve=False, is_arp_armature=False)

	# Select all bones
	bpy.ops.pose.select_all(action='SELECT')

	# Press Copy Selected Bone Rotation
	bpy.ops.arp.copy_bone_rest()

	# Press Apply
	bpy.ops.arp.copy_raw_coordinates()


	###
	### Re-Target source animation onto the target armature. 
	###

	# Press Re-Target equivalent.
	source_rig_name = scene.source_rig
	source_rig = scene.objects[source_rig_name]

	frame_range = source_rig.animation_data.action.frame_range
	frame_start = int(frame_range[0])
	frame_end = int(frame_range[1])

	bpy.ops.arp.retarget(frame_start = frame_start, frame_end = frame_end)
	
	# Push animation down to the NLA strip on the target rig.
	push_armature_action_to_new_nla_strip(target_rig, frame_start, anim_name, anim_name)

	delete_blender_obj(source_rig)