import type { Flowsheet, Results } from '@/lib/digital-engineer/contracts';
import { streamColumns, streamRows } from '@/lib/digital-engineer/stream-table';
import styles from './workspace.module.css';

const format = new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 });
export function StreamTable({
  flowsheet,
  results,
}: {
  flowsheet: Flowsheet;
  results: Results | null;
}) {
  const columns = streamColumns(flowsheet, results);
  return (
    <section aria-labelledby="stream-table-title">
      <h3 id="stream-table-title">Engineering Stream Table</h3>
      <p>
        {columns.every((c) => c.result)
          ? 'Current engineering results.'
          : 'Awaiting current calculation. Only available specified feed conditions and component flows are shown.'}{' '}
        Composition is on a mass-fraction basis (kg/kg); molar composition is not calculated by the
        current model.
      </p>
      <div className={styles.tableWrap}>
        <table aria-label="Engineering Stream Table">
          <thead>
            <tr>
              <th scope="col">Property</th>
              <th scope="col">Unit / basis</th>
              {columns.map(({ stream }) => (
                <th scope="col" key={stream.id} data-stream-id={stream.id}>
                  {'engineering_number' in stream ? String(stream.engineering_number) : '—'}{' '}
                  {stream.service.toUpperCase()}
                  <br />
                  <small>ID: {stream.id}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {streamRows(flowsheet).map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                <td>{row.unit}</td>
                {columns.map((column) => {
                  const value = row.value(column);
                  return (
                    <td
                      key={column.stream.id}
                      data-stream-id={column.stream.id}
                      title={
                        value === null
                          ? 'Not calculated by the active engineering model'
                          : String(value)
                      }
                    >
                      {value === null
                        ? '—'
                        : typeof value === 'number'
                          ? format.format(value)
                          : value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        — = not calculated by the active engineering model. Zero is a specified or calculated value.
      </p>
      {flowsheet.schema_version === '1.0' && (
        <p>Regenerate the PFD to assign engineering stream numbers.</p>
      )}
    </section>
  );
}
