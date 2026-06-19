// Shared pocket and horn geometry for standard size hobby servos
// (DS3225, MG996R class: 40.7 x 20.5 body, 49 mm tab hole spacing).

include <common.scad>

servo_l = 40.9;
servo_w = 20.7;
servo_tab_span = 49.2;
servo_tab_hole = 4.3;
servo_horn_circle = 21;   // round horn diameter
horn_screw = 2.6;

module servo_pocket(depth = 26) {
    // Cut this from a solid to seat a servo, tabs resting on the face
    translate([0, 0, -depth]) linear_extrude(depth + 0.01)
        square([servo_l, servo_w], center = true);
    for (x = [-servo_tab_span / 2, servo_tab_span / 2])
        translate([x, 0, -depth]) cylinder(d = servo_tab_hole, h = depth + 10);
}

module horn_holes(t) {
    // Centre screw plus 4 horn screws on a 14 mm circle
    hole(3.2, t);
    for (a = [0, 90, 180, 270])
        rotate([0, 0, a]) translate([7, 0, 0]) hole(horn_screw, t);
}
