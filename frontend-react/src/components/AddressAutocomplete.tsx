import { useState, useEffect, useRef } from 'react';
import {
  TextField,
  Autocomplete as MuiAutocomplete,
  CircularProgress,
  type TextFieldProps,
} from '@mui/material';

interface AddressSuggestion {
  properties: {
    name?: string;
    street?: string;
    housenumber?: string;
    city?: string;
    state?: string;
    postcode?: string;
    country?: string;
  };
  geometry: {
    coordinates: [number, number];
  };
}

interface AddressAutocompleteProps {
  value: string;
  onChange: (address: string) => void;
  textFieldProps?: Omit<TextFieldProps, 'value' | 'onChange'>;
}

const AddressAutocomplete = ({ value, onChange, textFieldProps }: AddressAutocompleteProps) => {
  const [options, setOptions] = useState<AddressSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Fetch suggestions from Photon API (OpenStreetMap geocoder)
  const fetchSuggestions = async (query: string) => {
    if (query.length < 3) {
      setOptions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5&countrycodes=us`
      );
      const data = await response.json();
      setOptions(data.features || []);
    } catch (error) {
      console.error('Error fetching address suggestions:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  // Debounce the API calls
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(inputValue);
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [inputValue]);

  // Format the suggestion for display
  const formatSuggestion = (suggestion: AddressSuggestion): string => {
    const { properties } = suggestion;
    const parts = [
      properties.housenumber,
      properties.street || properties.name,
      properties.city,
      properties.state,
      properties.postcode,
    ].filter(Boolean);
    return parts.join(', ');
  };

  return (
    <MuiAutocomplete
      freeSolo
      options={options}
      loading={loading}
      inputValue={inputValue}
      onInputChange={(event, newValue, reason) => {
        // Only update if user is typing (not when selecting from dropdown)
        if (reason === 'input') {
          setInputValue(newValue);
          onChange(newValue);
        }
      }}
      onChange={(_, newValue) => {
        if (newValue && typeof newValue === 'object') {
          const formatted = formatSuggestion(newValue as AddressSuggestion);
          setInputValue(formatted);
          onChange(formatted);
          setOptions([]); // Clear options after selection
        }
      }}
      getOptionLabel={(option) => {
        if (typeof option === 'string') return option;
        return formatSuggestion(option as AddressSuggestion);
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          {...textFieldProps}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      filterOptions={(x) => x} // Don't filter, use API results as-is
      blurOnSelect
      clearOnBlur={false}
    />
  );
};

export default AddressAutocomplete;
