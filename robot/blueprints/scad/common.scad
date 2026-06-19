// KARAKURI shared parameters and helpers
// All dimensions in millimetres. Holes are printed undersize-safe:
// M3 through 3.4, M4 through 4.5, M2.5 through 2.9, quarter-inch 6.6.

$fn = 64;

m2_5 = 2.9;
m3 = 3.4;
m4 = 4.5;
quarter_inch = 6.6;

module rounded_plate(x, y, t, r = 8) {
    linear_extrude(t)
        offset(r = r) offset(delta = -r)
            square([x, y], center = true);
}

module hole(d, h) {
    translate([0, 0, -0.5]) cylinder(d = d, h = h + 1);
}

module slot(d, len, h) {
    translate([0, 0, -0.5])
        linear_extrude(h + 1)
            hull() {
                translate([-len / 2, 0]) circle(d = d);
                translate([ len / 2, 0]) circle(d = d);
            }
}

module four_holes(dx, dy, d, h) {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * dx / 2, sy * dy / 2, 0]) hole(d, h);
}
