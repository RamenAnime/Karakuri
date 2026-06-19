// Tapered hose coupler between the nozzle port and the donor vacuum
// hose. Defaults join the 35 mm nozzle port to a 32 mm hose cuff,
// which suits the Bissell Featherweight and most Walmart stick vac
// hoses. Measure your donor's hose inner diameter and set hose_id
// before printing. A wrap of electrical tape fine tunes the fit.

include <common.scad>

port_od = 35.0;     // the nozzle port outer diameter this sleeves over
socket_id = 35.4;   // slip fit over the port
hose_id = 31.5;     // slides inside the donor hose cuff
wall_t = 2.8;
seg_len = 30;

module hose_coupler() {
    difference() {
        union() {
            cylinder(d = socket_id + 2 * wall_t, h = seg_len);          // socket sleeve
            translate([0, 0, seg_len]) cylinder(d = socket_id + 2 * wall_t + 4, h = 6);
            translate([0, 0, seg_len + 6])
                cylinder(d1 = hose_id + 2, d2 = hose_id, h = seg_len);  // hose taper
        }
        // socket pocket that swallows the port
        translate([0, 0, -0.5]) cylinder(d = socket_id, h = seg_len - 3 + 0.5);
        // continuous air bore matching the port inner diameter
        translate([0, 0, -0.5]) cylinder(d = hose_id - 2 * wall_t, h = 2 * seg_len + 8);
    }
}

hose_coupler();
