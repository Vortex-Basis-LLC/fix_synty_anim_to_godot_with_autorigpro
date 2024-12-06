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
import os
import re

from typing import List, Dict

from . import retarget_helpers
from . import anim_file_crawler

AnimMetadataOrganizer = anim_file_crawler.AnimMetadataOrganizer
AnimFileEntryMetadata = anim_file_crawler.AnimFileEntryMetadata
AnimFileEntry = anim_file_crawler.AnimFileEntry
AnimFileCrawler = anim_file_crawler.AnimFileCrawler
AnimFileEntryMetadataProcessor = anim_file_crawler.AnimFileEntryMetadataProcessor



def clean_group_name_to_be_filename(string):
    return re.sub(r'[^a-zA-Z0-9_-]', '', string)

class SCENE_OP_retarget_batcher(bpy.types.Operator):
	"""Retarget a series of animations onto a target rig."""

	bl_idname = 'fix_synty_anim_to_godot_with_autorigpro.retarget'
	bl_label = 'Batch Retarget'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		# TODO: Ensure Auto-Rig Pro has been configured with target rig and bone map.
		return context.mode == 'OBJECT'
	

	def execute(self, context):
		base_module_path = os.path.dirname(__file__)

		scene = bpy.context.scene

		anim_config_csv_path = scene.fix_synty_with_arp_anim_config_csv
		if anim_config_csv_path == '':
			scene.fix_synty_with_arp_anim_config_csv = os.path.join(base_module_path, 'synty_anim_metadata.csv')
			self.report({'INFO', 'Anim Config not set. Default one has been suggested.'})
			return {'CANCELLED'}

		if not os.path.exists(anim_config_csv_path):
			self.report({'ERROR'}, 'Anim Config CSV path not specified.')
			return {'CANCELLED'}

		if not os.path.exists(bpy.context.scene.fix_synty_with_arp_import_path):
			self.report({'ERROR'}, 'Import path not specified.')
			return {'CANCELLED'}
		
		if not os.path.exists(bpy.context.scene.fix_synty_with_arp_export_path):
				self.report({'ERROR'}, f'Export path not specified.')
				return {'CANCELLED'}

		anim_entries = []
		anim_crawler = AnimFileCrawler(os.path.join(bpy.context.scene.fix_synty_with_arp_import_path))
		anim_crawler.crawl_folders_for_anims(anim_crawler.root_path, anim_entries)

		ignore_root_motion = scene.fix_synty_with_arp_ignore_root_motion
		anim_metadata_list = AnimFileEntryMetadataProcessor.load_metadata_list(anim_config_csv_path, ignore_root_motion)

		# Find t-pose FBX file.
		tpose_metadata: AnimFileEntryMetadata = None
		for anim_metadata in anim_metadata_list:
			if anim_metadata.tags == 'tpose':
				tpose_metadata = anim_metadata
				break

		anim_metadata_organizer = AnimMetadataOrganizer()
		anim_metadata_organizer.set_anim_metadata_list(anim_metadata_list)

		for entry in anim_entries:
			anim_entry: AnimFileEntry = entry
			anim_metadata_entry = anim_metadata_organizer.try_find_anim_metadata_for_entry(anim_entry)
			if anim_metadata_entry is not None:
				anim_entry.should_loop = anim_metadata_entry.loop
				anim_metadata_organizer.add_to_group(anim_metadata_entry.group, anim_entry)
		
		target_rig_name = scene.target_rig
		target_rig = scene.objects.get(target_rig_name)

		if target_rig is None:
			# If the scene is empty, we can try to auto-load the t-pose anim as the target.
			if len(scene.objects) == 0:
				tpose_file_entry = anim_metadata_organizer.get_tpose_anim_file_entry()
				if not tpose_file_entry is None:
					bpy.ops.import_scene.fbx(filepath=tpose_file_entry.full_path, automatic_bone_orientation=True, ignore_leaf_bones=True)
					target_rig = context.active_object
					target_rig_name = target_rig.name
					scene.target_rig = target_rig_name
					scene.source_rig = target_rig_name

					# Import bone mapping for target rig armature.
					bpy.ops.arp.build_bones_list()

					# Import the default bone map for Synty armature.
					synty_bonemap_path =  os.path.join(base_module_path, 'synty_remap_preset.bmap')
					print("Attempting to load bonemap path: " + synty_bonemap_path)
					try:
						bpy.ops.arp.import_config(filepath=synty_bonemap_path)
					except:
						print("Some bones probably just didn't exist in both armatures.")
				else: 
					print("No T-pose FBX found.")

		if target_rig is None:
			self.report({'ERROR'}, 'Auto-Rig Pro Remap target armature not set.')
			return {'CANCELLED'}

		# Confirm that bone map has been set up in Auto-Rig Pro.
		if len(bpy.context.scene.bones_map_v2) == 0:
			self.report({'ERROR'}, 'Auto-Rig Pro Remap bone map is not configured.')
			return {'CANCELLED'}

		for group in anim_metadata_organizer.get_group_names():
			print('>>> Starting group: ' + group)

			group_file_entries = anim_metadata_organizer.get_anim_file_entries_for_group(group)

			# Clear current NLA tracks, so that we only have the new NLA tracks we're importing for this set.
			retarget_helpers.delete_all_nla_tracks_on_armature(target_rig)

			for anim_file_entry in group_file_entries:
				base_file_name = os.path.splitext(os.path.basename(anim_file_entry.full_path))[0]
				anim_name = base_file_name
				if anim_file_entry.should_loop and not anim_name.endswith('-loop'):
					anim_name += '-loop'
				retarget_helpers.push_fbx_animation_to_target_rig_nla_track(anim_file_entry.full_path, anim_name)
				
			# Remove unexpected characters to avoid unexpected hack attempts based on file name escape sequences.
			sanitized_group_name = clean_group_name_to_be_filename(group)
			full_export_path = os.path.join(bpy.context.scene.fix_synty_with_arp_export_path, sanitized_group_name + '.glb')

			bpy.ops.export_scene.gltf(
				filepath=full_export_path,
				export_format='GLB',
				export_animation_mode='NLA_TRACKS',
				export_materials='NONE',
				export_reset_pose_bones=True
			) 
			
			print("Purge unused data...")
			bpy.ops.outliner.orphans_purge()

		self.report({'INFO'}, f'Exports finished.')
		return {'FINISHED'}


class VIEW3D_PT_fix_synty_anim_to_godot_with_autorigpro(bpy.types.Panel):
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'Fix Synty Anim To Godot With ARP'
		bl_label = 'Fix Synty Anim To Godot With ARP'

		def draw(self, context):
			layout = self.layout

			row = layout.row()
			row.label(text='Anim Config CSV')
			row = layout.row()
			row.prop(context.scene, 'fix_synty_with_arp_anim_config_csv', text='')

			row = layout.row()
			row.prop(context.scene, 'fix_synty_with_arp_ignore_root_motion')

			row = layout.row()
			row.label(text='Import Path')
			row = layout.row()
			row.prop(context.scene, 'fix_synty_with_arp_import_path', text='')
			
			row = layout.row()
			row.label(text='Export Path')
			row = layout.row()
			row.prop(context.scene, 'fix_synty_with_arp_export_path', text='')

			row = layout.row()
			layout.operator('fix_synty_anim_to_godot_with_autorigpro.retarget')


classes = [SCENE_OP_retarget_batcher, VIEW3D_PT_fix_synty_anim_to_godot_with_autorigpro]

def register():
	bpy.types.Scene.fix_synty_with_arp_anim_config_csv = bpy.props.StringProperty(
		name = 'Anim Config CSV',
		description="Choose CSV file with animation configurations.",
		default='',
		subtype='FILE_PATH')
	
	bpy.types.Scene.fix_synty_with_arp_ignore_root_motion = bpy.props.BoolProperty(
		name = 'Ignore Root Motion',
		description='Animations marked as root_motion in config will be ignore. Root motion conversions do not quite work yet.',
		default=True)

	bpy.types.Scene.fix_synty_with_arp_import_path = bpy.props.StringProperty(
		name = 'Import Path',
		description="Choose a directory for animations.",
		default='',
		subtype='DIR_PATH')

	bpy.types.Scene.fix_synty_with_arp_export_path = bpy.props.StringProperty(
		name = 'Export Path',
		description='Choose a directory for exports.',
		default='',
		subtype='DIR_PATH')

	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	del bpy.types.Scene.fix_synty_with_arp_export_path
	del bpy.types.Scene.fix_synty_with_arp_import_path
	del bpy.types.Scene.fix_synty_with_arp_anim_config_csv
