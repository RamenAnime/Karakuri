// Camera mast column. 40 x 40 box section, 230 mm tall with a flange
// at each end. Print one for a 230 mm camera height or stack two for
// 460 mm. The Kinect v2 cannot resolve depth closer than about 0.5 m,
// so two stacked columns put the sensor high enough that the floor
// directly in front of the robot stays inside its working range.
// Prints vertically, no supports; use a brim.

include <common.scad>

col = 40;
wall_t = 4;
height = 230;
flange = 70;
flange_t = 6;

module flange_plate() {
    difference() {
        rounded_plate(flange, flange, flange_t, 6);
        four_holes(50, 50, m4, flange_t);
    }
}

module mast_column() {
    flange_plate();
    translate([0, 0, height - flange_t]) flange_plate();
    difference() {
        linear_extrude(height) square([col, col], center = true);
        translate([0, 0, flange_t])
            linear_extrude(height - 2 * flange_t)
                square([col - 2 * wall_t, col - 2 * wall_t], center = true);
        // Cable window front and back
        for (a = [0, 180])
            rotate([0, 0, a])
                translate([0, col / 2 + 1, height / 2])
                    rotate([90, 0, 0]) slot(16, 60, col);
    }
}

mast_column();
