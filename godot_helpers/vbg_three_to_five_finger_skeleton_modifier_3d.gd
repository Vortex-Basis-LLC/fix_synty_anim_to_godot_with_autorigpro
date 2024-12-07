# MIT License

# Copyright (c) 2024 Vortex Basis, LLC

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

@tool
class_name VbgThreeToFiveFingerSkeletonModifier3D extends SkeletonModifier3D

# Some simple animation packages only animate 3 fingers per hand. Usually, the ring
# and little finger are just in same position as the middle finger though, so this
# skeleton modifier just copies the rotations from the middle finger to the ring
# and little fingers to allow 3-fingered animations to be used on 5-fingered models.

var left_middle_proximal_bone: int
var left_middle_intermediate_bone: int
var left_middle_distal_bone: int

var left_ring_proximal_bone: int
var left_ring_intermediate_bone: int
var left_ring_distal_bone: int

var left_little_proximal_bone: int
var left_little_intermediate_bone: int
var left_little_distal_bone: int

var right_middle_proximal_bone: int
var right_middle_intermediate_bone: int
var right_middle_distal_bone: int

var right_ring_proximal_bone: int
var right_ring_intermediate_bone: int
var right_ring_distal_bone: int

var right_little_proximal_bone: int
var right_little_intermediate_bone: int
var right_little_distal_bone: int


func _ready() -> void:
	refresh_bone_indexes()

func refresh_bone_indexes():
	var skeleton := get_skeleton()

	left_middle_proximal_bone = skeleton.find_bone("LeftMiddleProximal")
	left_middle_intermediate_bone = skeleton.find_bone("LeftMiddleIntermediate")
	left_middle_distal_bone = skeleton.find_bone("LeftMiddleIntermediate")

	left_ring_proximal_bone = skeleton.find_bone("LeftRingProximal")
	left_ring_intermediate_bone = skeleton.find_bone("LeftRingIntermediate")
	left_ring_distal_bone = skeleton.find_bone("LeftRingDistal")

	left_little_proximal_bone = skeleton.find_bone("LeftLittleProximal")
	left_little_intermediate_bone = skeleton.find_bone("LeftLittleIntermediate")
	left_little_distal_bone = skeleton.find_bone("LeftLittleDistal")

	right_middle_proximal_bone = skeleton.find_bone("RightMiddleProximal")
	right_middle_intermediate_bone = skeleton.find_bone("RightMiddleIntermediate")
	right_middle_distal_bone = skeleton.find_bone("RightMiddleIntermediate")

	right_ring_proximal_bone = skeleton.find_bone("RightRingProximal")
	right_ring_intermediate_bone = skeleton.find_bone("RightRingIntermediate")
	right_ring_distal_bone = skeleton.find_bone("RightRingDistal")

	right_little_proximal_bone = skeleton.find_bone("RightLittleProximal")
	right_little_intermediate_bone = skeleton.find_bone("RightLittleIntermediate")
	right_little_distal_bone = skeleton.find_bone("RightLittleDistal")



func _process_modification() -> void:
	var skeleton := get_skeleton()

	# Get rotations of left middle finger.
	var left_middle_proximal_pose_rotation := skeleton.get_bone_pose_rotation(left_middle_proximal_bone)
	var left_middle_intermediate_pose_rotation := skeleton.get_bone_pose_rotation(left_middle_intermediate_bone)
	var left_middle_distal_pose_rotation := skeleton.get_bone_pose_rotation(left_middle_distal_bone)

	# Use same rotations on the left ring and little finger.
	skeleton.set_bone_pose_rotation(left_ring_proximal_bone, left_middle_proximal_pose_rotation)
	skeleton.set_bone_pose_rotation(left_ring_intermediate_bone, left_middle_intermediate_pose_rotation)
	skeleton.set_bone_pose_rotation(left_ring_distal_bone, left_middle_distal_pose_rotation)

	skeleton.set_bone_pose_rotation(left_little_proximal_bone, left_middle_proximal_pose_rotation)
	skeleton.set_bone_pose_rotation(left_little_intermediate_bone, left_middle_intermediate_pose_rotation)
	skeleton.set_bone_pose_rotation(left_little_distal_bone, left_middle_distal_pose_rotation)

	# Get rotations of right middle finger.
	var right_middle_proximal_pose_rotation := skeleton.get_bone_pose_rotation(right_middle_proximal_bone)
	var right_middle_intermediate_pose_rotation := skeleton.get_bone_pose_rotation(right_middle_intermediate_bone)
	var right_middle_distal_pose_rotation := skeleton.get_bone_pose_rotation(right_middle_distal_bone)

	# Use same rotations on the ring ring and little finger.
	skeleton.set_bone_pose_rotation(right_ring_proximal_bone, right_middle_proximal_pose_rotation)
	skeleton.set_bone_pose_rotation(right_ring_intermediate_bone, right_middle_intermediate_pose_rotation)
	skeleton.set_bone_pose_rotation(right_ring_distal_bone, right_middle_distal_pose_rotation)

	skeleton.set_bone_pose_rotation(right_little_proximal_bone, right_middle_proximal_pose_rotation)
	skeleton.set_bone_pose_rotation(right_little_intermediate_bone, right_middle_intermediate_pose_rotation)
	skeleton.set_bone_pose_rotation(right_little_distal_bone, right_middle_distal_pose_rotation)
