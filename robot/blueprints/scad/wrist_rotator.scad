// Continuous rotation wrist. A 360 modified servo sits in the carrier;
// its horn bolts to the rotator hub, and the gripper palm bolts to the
// hub face. Because the servo is continuous, the claw spins without
// limit for full dexterity. Print both pieces flat.
include <servo_common.scad>

module wrist_carrier() {
    difference() {
        linear_extrude(30)
            offset(r = 3) offset(delta = -3)
                square([servo_w + 12, servo_l + 12], center = true);
        translate([0, 0, 30]) rotate([0, 0, 90]) servo_pocket(28);
        // bolts sideways to the forearm link carrier
        for (z = [8, 20])
            translate([0, 0, z]) rotate([90, 0, 0])
                translate([0, 0, -(servo_l + 14) / 2]) cylinder(d = m3, h = servo_l + 14);
    }
}
module wrist_hub() {
    difference() {
        cylinder(d = 44, h = 6);
        horn_holes(6);
        four_holes(30, 30, m3, 6);   // palm bolts
    }
}
wrist_carrier();
translate([60, 0, 0]) wrist_hub();
