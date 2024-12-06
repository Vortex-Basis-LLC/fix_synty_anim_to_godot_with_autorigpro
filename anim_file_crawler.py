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

from typing import List

from dataclasses import dataclass, asdict
import csv


# For the line items in the metadata file.
@dataclass
class AnimFileEntryMetadata:
	filename: str
	group: str
	loop: bool
	root_motion: bool
	tags: str
	orig_path: str


class AnimFileEntry:
	full_path: str = ''
	relative_path: str = ''
	base_name: str = ''
	should_loop: bool = False


class AnimFileCrawler:
	root_path = ''
	filename_must_have = None
	filename_must_not_have = None
	
	def __init__(
			self,
			root_path, 
			loop = False, 
			filename_must_have = None,
			filename_must_not_have = None
		):
		self.root_path = root_path
		self.loop = loop
		self.filename_must_have = filename_must_have
		self.filename_must_not_have = filename_must_not_have


	def crawl_folders_for_anims(self, folder_path, out_entries):
		path_contents = os.listdir(folder_path)
		for filename in path_contents:
			filename_lower = filename.lower()
			
			full_path = os.path.join(folder_path, filename)
			if os.path.isdir(full_path):
				self.crawl_folders_for_anims(full_path, out_entries)
			elif filename_lower.endswith('.fbx'):
				include = True
				
				if self.filename_must_have is not None:
					if self.filename_must_have.lower() not in filename_lower:
						include = False
						
				if self.filename_must_not_have is not None:
					if self.filename_must_not_have.lower() in filename_lower:
						include = False
				
				if include:
					entry = AnimFileEntry()
					entry.full_path = full_path
					entry.relative_path = os.path.relpath(full_path, self.root_path)
					entry.base_name = os.path.basename(full_path)
					entry.should_loop = self.should_loop(full_path)
					out_entries.append(entry)


	def should_loop(self, filepath):
		# TODO: Add way to specify rule list or overrides...
		basename = os.path.basename(filepath).lower()
		if '_to_' in basename:
			return False
		if 'jump' in basename:
			return False

		if 'walk' in basename:
			return True
		if 'sprint' in basename:
			return True
		if 'shuffle' in basename:
			return True
		if 'turn' in basename:
			return True
		if 'idle' in basename:
			return True
		
		return False


# Reads and writes CSV files for animation data metadata.
class AnimFileEntryMetadataProcessor:
	@staticmethod
	def load_metadata_list(csv_filename: str, ignore_root_motion: bool) -> List[AnimFileEntryMetadata]:
		list: List[AnimFileEntryMetadata] = []
		
		with open(csv_filename, 'r') as in_file:
			csv_reader = csv.DictReader(in_file)
			for row in csv_reader:
				metadata = AnimFileEntryMetadata(
					filename=row['filename'],
					group=row['group'],
					loop=row['loop'] == 'TRUE',
					root_motion=row['root_motion'] == 'TRUE',
					tags=row['tags'],
					orig_path=row['orig_path']
				)
				if not ignore_root_motion or not metadata.root_motion:
					list.append(metadata)

		return list
	
	@staticmethod
	def save_metadata_list(csv_filename: str, entry_list: List[AnimFileEntryMetadata]) -> None:
		with open(csv_filename, 'w', newline='') as out_file:
			fieldnames = ['filename', 'group', 'loop', 'root_motion', 'tags', 'orig_path']
			csv_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
			csv_writer.writeheader()
			for entry in entry_list:
				csv_writer.writerow(asdict(entry))

	@staticmethod
	def build_metadata_list_template_from_folder(root_path: str) -> List[AnimFileEntryMetadata]:
		anim_entries = []
		anim_crawler = AnimFileCrawler(root_path)
		anim_crawler.crawl_folders_for_anims(anim_crawler.root_path, anim_entries)

		anim_metadata_list: List[AnimFileEntryMetadata] = []
		for entry in anim_entries:
			anim_entry: AnimFileEntry = entry
			anim_metadata_list.append(AnimFileEntryMetadata(
				filename=anim_entry.base_name,
				group=anim_entry.relative_path,
				loop=anim_entry.should_loop,
				tags='',
				orig_path=entry.relative_path
			))

		return anim_metadata_list



class AnimMetadataGroup:
	group: str
	entries: List[AnimFileEntry]

# Organizes and groups the animation metadata and pairs with actual files found.
class AnimMetadataOrganizer:
	_group_map: dict
	_anim_metadata_list: List[AnimFileEntryMetadata]

	_tpose_metadata: AnimFileEntryMetadata = None
	_tpose_file_entry: AnimFileEntry = None

	def __init__(self):
		self._group_map = {}


	def set_anim_metadata_list(self, anim_metadata_list: List[AnimFileEntryMetadata]) -> None:
		self._anim_metadata_list = anim_metadata_list

		tpose_metadata: AnimFileEntryMetadata = None
		for anim_metadata in anim_metadata_list:
			# TODO: If ever using multiple tags, would need to split tags before check here.
			if anim_metadata.tags == 'tpose':
				tpose_metadata = anim_metadata
				break

		self._tpose_metadata = tpose_metadata


	def try_find_anim_metadata_for_entry(self, anim_entry: AnimFileEntry) -> AnimFileEntryMetadata:
		for metadata in self._anim_metadata_list:
			if metadata.filename == anim_entry.base_name:
				return metadata
			
		return None
	

	def add_to_group(self, group: str, anim_entry: AnimFileEntry) -> None:
		metadata_group: AnimMetadataGroup = self._group_map.get(group)
		if metadata_group is None:
			metadata_group = AnimMetadataGroup()
			metadata_group.group = group
			metadata_group.entries = []
			self._group_map[group] = metadata_group

		# If we still need the tpose, see if this is the file for that one.
		if self._tpose_file_entry is None:
			metadata_entry = self.try_find_anim_metadata_for_entry(anim_entry)
			if metadata_entry == self._tpose_metadata:
				self._tpose_file_entry = anim_entry

		metadata_group.entries.append(anim_entry)

	def get_group_names(self):
		return self._group_map.keys()
	
	def get_anim_file_entries_for_group(self, group) -> List[AnimFileEntry]:
		metadata_group: AnimMetadataGroup = self._group_map.get(group)
		if metadata_group is None:
			return []
		else:
			return metadata_group.entries
	
	def get_tpose_anim_metadata_entry(self) -> AnimFileEntryMetadata:
		return self._tpose_metadata

	def get_tpose_anim_file_entry(self) -> AnimFileEntry:
		return self._tpose_file_entry