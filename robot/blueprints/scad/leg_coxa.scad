// Coxa: short link from the hip servo horn to the femur servo, which
// it carries rotated 90 degrees so the femur swings vertically.
// Print 4, flat down, no supports.
include <servo_common.scad>

coxa_len = 34;

module leg_coxa() {
    difference() {
        union() {
            cylinder(d = servo_horn_circle + 10, h = 6);
            translate([0, -((servo_w + 10) / 2), 0])
                linear_extrude(6)
                    translate([coxa_len / 2, (servo_w + 10) / 2])
                        square([coxa_len + 16, servo_w + 10], center = true);
            translate([coxa_len + 4, 0, 6]) linear_extrude(28)
                offset(r = 3) offset(delta = -3)
                    square([servo_w + 10, servo_l + 10], center = true);
        }
        horn_holes(6);
        translate([coxa_len + 4, 0, 34]) rotate([0, 0, 90]) servo_pocket(30);
    }
}
leg_coxa();
