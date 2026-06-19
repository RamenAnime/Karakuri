// Heavy limb link for thigh and shin, print 4. 100 mm between centres,
// twin ribs for stiffness under the robot's standing load. Horn disc
// one end, servo carrier the other, same convention as the arm links.
include <servo_common.scad>

llen = 100;

module limb_link_heavy() {
    difference() {
        union() {
            hull() {
                cylinder(d = servo_horn_circle + 14, h = 8);
                translate([llen, 0, 0]) cylinder(d = servo_w + 16, h = 8);
            }
            for (s = [-1, 1])
                translate([12, s * 14, 8]) cube([llen - 30, 5, 8]);
            translate([llen, 0, 8]) linear_extrude(30)
                offset(r=3) offset(delta=-3) square([servo_w + 14, servo_l + 14], center = true);
        }
        horn_holes(8);
        translate([llen, 0, 38]) rotate([0, 0, 90]) servo_pocket(30);
        for (x = [32, 52, 72]) translate([x, 0, 0]) hole(12, 8);
    }
}
limb_link_heavy();
