// Chest corner post, print 4. 120 mm tall, M4 tapped-by-bolt both ends,
// shoulder-side posts also expose the 50 mm M4 square pattern halfway
// up for the biaxial shoulder joints.
include <common.scad>

module chest_post() {
    difference() {
        linear_extrude(120) offset(r=3) offset(delta=-3) square([22, 22], center = true);
        translate([0, 0, -0.5]) cylinder(d = 3.4, h = 30);          // M4 self-thread bottom
        translate([0, 0, 90.5]) cylinder(d = 3.4, h = 30);          // top
        // side face shoulder square (use on the two front posts)
        for (z = [35, 85]) for (y = [-1, 1])
            translate([0, y * 25, z]) rotate([90, 0, 0]) translate([0,0,-14]) cylinder(d = m4, h = 28);
    }
}
chest_post();
