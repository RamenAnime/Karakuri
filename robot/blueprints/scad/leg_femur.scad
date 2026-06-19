// Femur: 80 mm link, servo horn disc at the hip end, knee servo
// carrier at the far end. Print 4 flat, no supports.
include <servo_common.scad>

femur = 80;

module leg_femur() {
    difference() {
        union() {
            hull() {
                cylinder(d = servo_horn_circle + 10, h = 6);
                translate([femur, 0, 0]) cylinder(d = servo_w + 12, h = 6);
            }
            translate([femur, 0, 6]) linear_extrude(28)
                offset(r = 3) offset(delta = -3)
                    square([servo_w + 10, servo_l + 10], center = true);
        }
        horn_holes(6);
        translate([femur, 0, 34]) rotate([0, 0, 90]) servo_pocket(30);
        // lightening holes
        for (x = [25, 45]) translate([x, 0, 0]) hole(10, 6);
    }
}
leg_femur();
