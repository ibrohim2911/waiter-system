import { useState, useEffect } from 'react';
import { places, tables } from '../services/placeSelection';

export const usePlaceSelection = () => {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [availableTables, setAvailableTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [isLoadingLocations, setIsLoadingLocations] = useState(false);
  const [isLoadingTables, setIsLoadingTables] = useState(false);
  const [error, setError] = useState(null);
  const [allTables, setAllTables] = useState([]);

  // Fetch all locations on mount
  const fetchLocations = async () => {
    try {
      setIsLoadingLocations(true);
      setError(null);
      
      const locationData = await places();
      const uniqueLocations = [...new Set(locationData)].filter(Boolean).sort();
      setLocations(uniqueLocations);
    } catch (err) {
      setError('Joylar yuklanmadi');
      console.error('Error fetching locations:', err);
    } finally {
      setIsLoadingLocations(false);
    }
  };

  // Fetch tables for selected location
  const fetchTablesForLocation = async (location) => {
    if (!location) {
      setAvailableTables([]);
      setSelectedTable(null);
      return;
    }

    try {
      setIsLoadingTables(true);
      setError(null);
      const tableData = await tables(location);
      setAvailableTables(tableData);
      // Reset selected table when location changes
      setSelectedTable(null);
    } catch (err) {
      setError('Stollar yuklanmadi');
      console.error('Error fetching tables:', err);
      setAvailableTables([]);
    } finally {
      setIsLoadingTables(false);
    }
  };

  // Handle location selection
  const selectLocation = (location) => {
    setSelectedLocation(location);
    if (location) {
      fetchTablesForLocation(location);
    } else {
      setAvailableTables([]);
      setSelectedTable(null);
    }
  };

  // Handle table selection
  const selectTable = (table) => {
    setSelectedTable(table);
  };

  // Reset all selections
  const resetSelection = () => {
    setSelectedLocation('');
    setSelectedTable(null);
    setAvailableTables([]);
    setError(null);
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // Get table count for a specific location
  const getTableCountForLocation = async (location) => {
    try {
      const tableData = await tables(location);
    return tableData.filter(table => table.is_available).length;
    } catch (err) {
      console.error('Error getting table count for location:', location, err);
      return 0;
    }
  };

  // Load locations on component mount
  useEffect(() => {
    fetchLocations();
  }, []);

  return {
    // State values
    locations,
    selectedLocation,
    availableTables,
    selectedTable,
    isLoadingLocations,
    isLoadingTables,
    error,
    allTables,
    
    // Actions
    selectLocation,
    selectTable,
    resetSelection,
    clearError,
    refetchLocations: fetchLocations,
    refetchTables: () => fetchTablesForLocation(selectedLocation),
    getTableCountForLocation,
    
    // Computed properties
    hasSelectedLocation: Boolean(selectedLocation),
    hasSelectedTable: Boolean(selectedTable),
    isSelectionComplete: Boolean(selectedLocation && selectedTable),
    isLoading: isLoadingLocations || isLoadingTables,
    
    // Helper methods
    getTableById: (id) => availableTables.find(table => table.id === id),
    getTablesByLocation: (location) => availableTables.filter(table => table.location === location)
  };
};

export default usePlaceSelection;