// Editable fields per record type, in the order they appear in the edit modal.
export const LOGIN_FIELDS = [
  { name: 'first_name', label: 'First Name', required: true },
  { name: 'last_name', label: 'Last Name', required: true },
  { name: 'email', label: 'E-mail Address', type: 'email' },
]

export const STUDENT_FIELDS = [
  { name: 'student_id', label: 'Student ID', required: true },
  { name: 'full_name', label: 'Full Name', required: true },
  { name: 'khmer_name', label: 'Khmer Name' },
  { name: 'sex', label: 'Sex', type: 'select', required: true, options: [['FEMALE', 'Female'], ['MALE', 'Male']] },
  { name: 'date_of_birth', label: 'Date of Birth', type: 'date', required: true },
  { name: 'frn', label: 'Family Reference Number' },
  { name: 'nationality_1', label: 'Nationality' },
  { name: 'nationality_2', label: 'Second Nationality' },
  { name: 'remark', label: 'Remark', type: 'textarea' },
]

export const PARENT_FIELDS = [
  { name: 'full_name', label: 'Full Name', required: true },
  { name: 'phone_1', label: 'Phone' },
  { name: 'phone_2', label: 'Second Phone' },
]
