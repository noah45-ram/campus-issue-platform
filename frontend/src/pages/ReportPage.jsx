import React, { useRef, useState } from 'react';
import { createIssue } from '../api';

const LOCATION_TYPES = [
  { value: 'hostel', label: 'Hostel' },
  { value: 'academic', label: 'Academic / Learning' },
  { value: 'library', label: 'Library' },
  { value: 'food', label: 'Cafeteria / Food Area' },
  { value: 'sports', label: 'Sports / Recreation' },
  { value: 'campus', label: 'Campus Grounds' },
  { value: 'administration', label: 'Administration / Services' },
  { value: 'other', label: 'Other Campus Area' },
];

const HOSTELS = ['H1', 'H2', 'H3', 'H4', 'H5'];
const WINGS = ['A', 'B'];
const FLOORS = ['1', '2', '3', '4', '5'];

const GENERAL_BUILDINGS = {
  academic: [
    'Academic Block A',
    'Academic Block B',
    'Academic Block C',
    'Academic Block D',
    'Academic Block E',
  ],
  library: ['Library'],
  food: ['Cafeteria / Food Area'],
  sports: ['Sports Complex'],
  campus: [
    'Main Gate',
    'Visitor Parking',
    'Amphitheatre',
    'Neem Forest',
    'Rain Water Harvesting Lake',
    'Other Campus Ground',
  ],
  administration: [
    'Administration / Reception',
    'Student Resource Centre',
    'Other Service Area',
  ],
  other: ['Other Building / Area'],
};

const GENERAL_AREAS = [
  'Room / Office',
  'Washroom',
  'Corridor',
  'Staircase',
  'Entrance / Exit',
  'Common Area',
  'Utility Area',
  'Electrical Area',
  'Outdoor Area',
  'Other',
];

const HOSTEL_AREAS = [
  'Room',
  'Washroom',
  'Corridor',
  'Staircase',
  'Common Area',
  'Study Area',
  'Utility Area',
  'Drinking Water Area',
  'Electrical Area',
  'Laundry Area',
  'Other',
];

const AFFECTED_AREA_OPTIONS = [
  { value: 'local', label: 'Local — single room / point' },
  { value: 'building', label: 'Building — wing / floor / block' },
  { value: 'campus', label: 'Campus — broad impact' },
];

function buildLocation(locationType, values) {
  if (locationType === 'hostel') {
    return [
      'Hostel Area',
      values.hostel,
      `Wing ${values.wing}`,
      `Floor ${values.floor}`,
      values.area,
      values.area === 'Room' || values.area === 'Other'
        ? values.specificArea.trim()
        : '',
    ]
      .filter(Boolean)
      .join(' — ');
  }

  return [
    LOCATION_TYPES.find((item) => item.value === locationType)?.label,
    values.building,
    values.area,
    values.area === 'Other' ? values.specificArea.trim() : '',
  ]
    .filter(Boolean)
    .join(' — ');
}

function SectionHeader({ number, title, description }) {
  return (
    <div className="report-section-header">
      <div className="report-step-number">{number}</div>
      <div>
        <h3 className="report-section-title">{title}</h3>
        {description && (
          <p className="report-section-description">{description}</p>
        )}
      </div>
    </div>
  );
}

export default function ReportPage({ onReportSubmitted }) {
  const fileInputRef = useRef(null);

  const [description, setDescription] = useState('');

  const [locationType, setLocationType] = useState('hostel');
  const [hostel, setHostel] = useState('H1');
  const [wing, setWing] = useState('A');
  const [floor, setFloor] = useState('1');
  const [building, setBuilding] = useState(GENERAL_BUILDINGS.academic[0]);
  const [area, setArea] = useState('Room');
  const [specificArea, setSpecificArea] = useState('');

  const [image, setImage] = useState(null);
  const [recurrence, setRecurrence] = useState(false);
  const [affectedArea, setAffectedArea] = useState('local');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const isHostel = locationType === 'hostel';
  const buildingOptions = GENERAL_BUILDINGS[locationType] || [];
  const areaOptions = isHostel ? HOSTEL_AREAS : GENERAL_AREAS;

  const handleLocationTypeChange = (value) => {
    setLocationType(value);
    setSpecificArea('');

    if (value === 'hostel') {
      setHostel('H1');
      setWing('A');
      setFloor('1');
      setArea('Room');
      return;
    }

    const buildings = GENERAL_BUILDINGS[value] || [];
    setBuilding(buildings[0] || '');
    setArea(value === 'campus' ? 'Outdoor Area' : 'Common Area');
  };

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Please upload a JPG, PNG, or WebP image.');
      event.target.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be 5 MB or smaller.');
      event.target.value = '';
      return;
    }

    setError('');
    setImage(file);
  };

  const removeImage = () => {
    setImage(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const cleanDescription = description.trim();

    if (!cleanDescription && !image) {
      setError('Add a short description or a photo showing the issue.');
      return;
    }

    if (
      (isHostel && (area === 'Room' || area === 'Other')) ||
      (!isHostel && area === 'Other')
    ) {
      if (!specificArea.trim()) {
        setError('Please specify the room or area.');
        return;
      }
    }

    const location = buildLocation(locationType, {
      hostel,
      wing,
      floor,
      building,
      area,
      specificArea,
    });

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await createIssue({
        description: cleanDescription,
        location,
        recurrence,
        affectedArea,
        image,
      });

      setResult(response);

      if (onReportSubmitted) {
        onReportSubmitted(response);
      }
    } catch (err) {
      setError(
        err.message ||
          'Failed to submit the report. Please check whether the backend is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const issue = result?.issue;
  const safety = issue?.safety || result?.safety;
  const priority = issue?.priority;

  return (
    <div className="report-page">
      <div className="report-intro">
        <div>
          <div className="eyebrow">CAMPUS OPERATIONS</div>
          <h1>Report a campus issue</h1>
          <p>
            Help the campus team identify and resolve safety, facility, water,
            energy and sustainability issues.
          </p>
        </div>

        <div className="report-intro-note">
          <span className="intro-note-dot" />
          <span>Reports are routed to the appropriate response team.</span>
        </div>
      </div>

      {error && (
        <div className="banner banner-critical report-error" role="alert">
          <div className="banner-icon">!</div>
          <div>
            <div className="banner-critical-title">Submission error</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      <form className="report-form" onSubmit={handleSubmit}>
        {/* STEP 1 */}
        <section className="report-section">
          <SectionHeader
            number="01"
            title="Describe the issue"
            description="Tell us what you observed. A short, factual description is enough."
          />

          <div className="report-section-body">
            <label htmlFor="issue-description" className="form-label">
              What did you notice?
            </label>

            <textarea
              id="issue-description"
              className="form-control report-textarea"
              placeholder="Example: Water is leaking continuously from a tap near the washroom."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              rows={5}
            />

            <div className="form-hint">
              Do not include names, phone numbers, or other personal information.
            </div>
          </div>
        </section>

        {/* STEP 2 */}
        <section className="report-section">
          <SectionHeader
            number="02"
            title="Tell us where it is"
            description="A precise location helps the maintenance team respond faster."
          />

          <div className="report-section-body">
            <div className="form-group">
              <label htmlFor="location-type" className="form-label">
                Campus area
              </label>

              <select
                id="location-type"
                className="form-control"
                value={locationType}
                onChange={(e) => handleLocationTypeChange(e.target.value)}
                disabled={loading}
              >
                {LOCATION_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>

            {isHostel ? (
              <div className="location-grid">
                <div className="form-group">
                  <label htmlFor="hostel" className="form-label">
                    Hostel
                  </label>

                  <select
                    id="hostel"
                    className="form-control"
                    value={hostel}
                    onChange={(e) => setHostel(e.target.value)}
                    disabled={loading}
                  >
                    {HOSTELS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="wing" className="form-label">
                    Wing
                  </label>

                  <select
                    id="wing"
                    className="form-control"
                    value={wing}
                    onChange={(e) => setWing(e.target.value)}
                    disabled={loading}
                  >
                    {WINGS.map((item) => (
                      <option key={item} value={item}>
                        Wing {item}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="floor" className="form-label">
                    Floor
                  </label>

                  <select
                    id="floor"
                    className="form-control"
                    value={floor}
                    onChange={(e) => setFloor(e.target.value)}
                    disabled={loading}
                  >
                    {FLOORS.map((item) => (
                      <option key={item} value={item}>
                        Floor {item}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div className="form-group">
                <label htmlFor="building" className="form-label">
                  Building / area
                </label>

                <select
                  id="building"
                  className="form-control"
                  value={building}
                  onChange={(e) => setBuilding(e.target.value)}
                  disabled={loading}
                >
                  {buildingOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="location-grid location-grid-secondary">
              <div className="form-group">
                <label htmlFor="specific-area-type" className="form-label">
                  Specific area
                </label>

                <select
                  id="specific-area-type"
                  className="form-control"
                  value={area}
                  onChange={(e) => {
                    setArea(e.target.value);

                    if (e.target.value !== 'Room' && e.target.value !== 'Other') {
                      setSpecificArea('');
                    }
                  }}
                  disabled={loading}
                >
                  {areaOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              {(area === 'Room' || area === 'Other') && (
                <div className="form-group">
                  <label htmlFor="specific-area" className="form-label">
                    {area === 'Room' ? 'Room number' : 'Specify area'}
                  </label>

                  <input
                    id="specific-area"
                    className="form-control"
                    value={specificArea}
                    onChange={(e) => setSpecificArea(e.target.value)}
                    placeholder={
                      area === 'Room'
                        ? 'Example: Room 305'
                        : 'Example: Water cooler beside Room 305'
                    }
                    disabled={loading}
                  />
                </div>
              )}
            </div>

            <div className="location-preview">
              <span className="location-preview-label">Selected location</span>
              <strong>
                {buildLocation(locationType, {
                  hostel,
                  wing,
                  floor,
                  building,
                  area,
                  specificArea: specificArea || '[not specified]',
                })}
              </strong>
            </div>
          </div>
        </section>

        {/* STEP 3 */}
        <section className="report-section">
          <SectionHeader
            number="03"
            title="Add evidence"
            description="A photo can help the response team understand the problem."
          />

          <div className="report-section-body">
            <input
              ref={fileInputRef}
              id="issue-image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleImageChange}
              disabled={loading}
              className="visually-hidden"
            />

            {!image ? (
              <button
                type="button"
                className="photo-upload-zone"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                <span className="upload-icon">+</span>

                <span className="upload-title">
                  Add photo evidence
                </span>

                <span className="upload-description">
                  Click to choose a JPG, PNG, or WebP image
                </span>

                <span className="upload-meta">
                  Optional · Maximum 5 MB
                </span>
              </button>
            ) : (
              <div className="photo-selected">
                <div className="photo-selected-icon">✓</div>

                <div className="photo-selected-info">
                  <strong>{image.name}</strong>
                  <span>
                    {(image.size / 1024 / 1024).toFixed(2)} MB · Photo evidence
                  </span>
                </div>

                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={removeImage}
                  disabled={loading}
                >
                  Remove
                </button>
              </div>
            )}

            <p className="evidence-note">
              Photos are used as supporting evidence only. The AI uses the
              written description for issue classification.
            </p>
          </div>
        </section>

        {/* STEP 4 */}
        <section className="report-section">
          <SectionHeader
            number="04"
            title="Help us understand the impact"
            description="These details help determine how the issue should be prioritized."
          />

          <div className="report-section-body">
            <div className="form-group">
              <label htmlFor="affected-area" className="form-label">
                How broadly does it affect the area?
              </label>

              <select
                id="affected-area"
                className="form-control"
                value={affectedArea}
                onChange={(e) => setAffectedArea(e.target.value)}
                disabled={loading}
              >
                {AFFECTED_AREA_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <label className="recurrence-control">
              <input
                type="checkbox"
                checked={recurrence}
                onChange={(e) => setRecurrence(e.target.checked)}
                disabled={loading}
              />

              <span className="recurrence-box">
                <strong>This has happened before</strong>
                <small>
                  Helps the system identify recurring campus problems.
                </small>
              </span>
            </label>
          </div>
        </section>

        {/* SUBMIT */}
        <div className="report-submit">
          <div>
            <strong>Ready to submit?</strong>
            <span>
              Your report will be classified and routed automatically.
            </span>
          </div>

          <button
            type="submit"
            className="btn btn-primary report-submit-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Submitting...
              </>
            ) : (
              'Report Issue'
            )}
          </button>
        </div>
      </form>

      {/* RESULT */}
      {result && (
        <section
          className="report-result"
          tabIndex="-1"
          id="report-result"
        >
          {safety?.is_safety_critical ? (
            <div className="result-safety">
              <div className="result-safety-icon">!</div>

              <div>
                <div className="result-eyebrow">IMMEDIATE ATTENTION</div>

                <h2>Safety alert detected</h2>

                <p>
                  {safety.message ||
                    'Move away from the hazard and do not attempt a repair.'}
                </p>
              </div>
            </div>
          ) : (
            <div className="result-success">
              <div className="result-success-icon">✓</div>

              <div>
                <div className="result-eyebrow">REPORT RECEIVED</div>

                <h2>
                  {result.action === 'linked_to_existing'
                    ? 'Your report was linked to an existing issue'
                    : 'Your issue has been reported'}
                </h2>

                <p>{result.message}</p>
              </div>
            </div>
          )}

          {safety?.alert_type === 'quick_action' && (
            <div className="quick-action">
              <div className="quick-action-label">QUICK ACTION</div>
              <strong>{safety.message}</strong>
            </div>
          )}

          {result.action === 'linked_to_existing' && (
            <div className="duplicate-note">
              <strong>Existing issue updated.</strong>
              <span>
                This report was grouped with the active issue rather than
                creating another maintenance ticket.
              </span>
              <span>
                Current report count: <strong>{issue?.report_count || 1}</strong>
              </span>
            </div>
          )}

          <div className="result-details">
            <div className="result-details-header">
              <div>
                <div className="result-eyebrow">ISSUE SUMMARY</div>
                <h3>{issue?.id || 'Issue'}</h3>
              </div>

              <span
                className={`badge badge-prio-${priority?.priority || 'low'}`}
              >
                {priority?.priority || 'low'} priority
              </span>
            </div>

            <div className="result-grid">
              <div>
                <span>Category</span>
                <strong>{issue?.category || 'Other'}</strong>
              </div>

              <div>
                <span>Status</span>
                <strong className="capitalize">
                  {issue?.status || 'open'}
                </strong>
              </div>

              <div>
                <span>Reports</span>
                <strong>{issue?.report_count || 1}</strong>
              </div>

              <div>
                <span>Location</span>
                <strong>{issue?.location || 'Not specified'}</strong>
              </div>
            </div>

            <div className="result-description">
              <span>Description</span>
              <p>
                {issue?.description ||
                  'Photo evidence submitted without description.'}
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
