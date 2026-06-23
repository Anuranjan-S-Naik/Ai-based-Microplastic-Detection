import React, { useMemo, useState } from "react";

const COLUMNS = [
  { key: "particle_id", label: "ID" },
  { key: "class", label: "Class" },
  { key: "confidence", label: "Conf." },
  { key: "length_um", label: "Length", alt: "length_px" },
  { key: "width_um", label: "Width", alt: "width_px" },
  { key: "area_um2", label: "Area", alt: "area_px" },
  { key: "aspect_ratio", label: "Aspect" },
  { key: "circularity", label: "Circ." },
  { key: "solidity", label: "Solidity" },
];

export default function ParticleTable({ particles, calibrated }) {
  const [sortKey, setSortKey] = useState("particle_id");
  const [asc, setAsc] = useState(true);

  const rows = useMemo(() => {
    const r = [...particles];
    r.sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (x === y) return 0;
      const cmp = x > y ? 1 : -1;
      return asc ? cmp : -cmp;
    });
    return r;
  }, [particles, sortKey, asc]);

  function toggleSort(key) {
    if (key === sortKey) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(true);
    }
  }

  function cellValue(row, col) {
    if (col.alt) {
      const k = calibrated && row[col.key] !== "" ? col.key : col.alt;
      return row[k];
    }
    return row[col.key];
  }

  return (
    <div className="table-wrap">
      <table className="ptable">
        <thead>
          <tr>
            {COLUMNS.map((c) => (
              <th key={c.key} onClick={() => toggleSort(c.key)}>
                {c.label}
                {sortKey === c.key ? (asc ? " ▲" : " ▼") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.particle_id}>
              {COLUMNS.map((c) => (
                <td key={c.key} className={c.key === "class" ? `cls-${row.class}` : ""}>
                  {cellValue(row, c)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
