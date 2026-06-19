// Parallel-ish claw. Palm carries a micro servo (MG90S pocket) whose
// horn drives one jaw; a printed gear sector on each jaw mirrors the
// motion. Jaw faces are ribbed for grip on plush toys. Print palm and
// two jaws flat, no supports.
include <servo_common.scad>

mg90_l = 23.2; mg90_w = 12.6; mg90_span = 28.0;

module gripper_palm() {
    difference() {
        rounded_plate(56, 64, 8, 6);
        four_holes(30, 30, m3, 8);              // to wrist hub
        // micro servo window
        translate([0, -10, 0]) {
            translate([0, 0, -0.5]) linear_extrude(9)
                square([mg90_l, mg90_w], center = true);
            for (x = [-mg90_span / 2, mg90_span / 2])
                translate([x, 0, 0]) hole(2.2, 8);
        }
        // jaw pivot holes
        for (x = [-16, 16]) translate([x, 22, 0]) hole(m3, 8);
    }
}
module gripper_jaw() {
    difference() {
        union() {
            // gear sector boss at the pivot
            cylinder(d = 22, h = 6);
            // curved finger
            translate([0, 0, 0]) linear_extrude(6)
                hull() {
                    circle(d = 18);
                    translate([6, 42]) circle(d = 10);
                }
            // grip ribs
            for (y = [18, 26, 34])
                translate([9, y, 6]) cylinder(d = 6, h = 3);
        }
        hole(m3, 12);
        // sector teeth approximated as drive pin holes
        for (a = [-30, 0, 30])
            rotate([0, 0, a]) translate([8.5, 0, 0]) hole(2.2, 6);
    }
}
gripper_palm();
translate([70, -20, 0]) gripper_jaw();
translate([110, -20, 0]) mirror([1, 0, 0]) gripper_jaw();
