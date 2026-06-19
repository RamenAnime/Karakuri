// Arm link, 120 mm between horn centres. Print 2: shoulder to elbow
// and elbow to wrist. Same pattern both ends: horn disc one end,
// servo carrier the other. Flat print, no supports.
include <servo_common.scad>

alink = 120;

module arm_link() {
    difference() {
        union() {
            hull() {
                cylinder(d = servo_horn_circle + 12, h = 7);
                translate([alink, 0, 0]) cylinder(d = servo_w + 14, h = 7);
            }
            translate([alink, 0, 7]) linear_extrude(28)
                offset(r = 3) offset(delta = -3)
                    square([servo_w + 12, servo_l + 12], center = true);
        }
        horn_holes(7);
        translate([alink, 0, 35]) rotate([0, 0, 90]) servo_pocket(30);
        for (x = [35, 60, 85]) translate([x, 0, 0]) hole(12, 7);
    }
}
arm_link();
