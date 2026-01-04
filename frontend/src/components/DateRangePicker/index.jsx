import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import { startOfWeek, endOfWeek, startOfMonth, endOfMonth } from 'date-fns';
import 'react-datepicker/dist/react-datepicker.css';

const DateRangePicker = ({ onChange }) => {
  const [period, setPeriod] = useState('day');
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [isTouch, setIsTouch] = useState(false);

  const handlePeriodChange = (newPeriod) => {
    if (newPeriod === 'limitless') {
      setPeriod('limitless');
      setStartDate(null);
      setEndDate(null);
      onChange({ period: 'alltime', startDate: null, endDate: null });
      return;
    }
    const now = new Date();
    let start = now;
    let end = now;

    if (newPeriod === 'week') {
      start = startOfWeek(now);
      end = endOfWeek(now);
    } else if (newPeriod === 'month') {
      start = startOfMonth(now);
      end = endOfMonth(now);
    }
    setPeriod(newPeriod);
    if (newPeriod !== 'custom') {
      setStartDate(start);
      setEndDate(end);
      onChange({ period: newPeriod, startDate: start, endDate: end });
    } else {
      onChange({ period: newPeriod, startDate, endDate });
    }
  };

  const handleStartDateChange = (date) => {
    setStartDate(date);
    setPeriod('custom');
    onChange({ period: 'custom', startDate: date, endDate });
  };

  const handleEndDateChange = (date) => {
    setEndDate(date);
    setPeriod('custom');
    onChange({ period: 'custom', startDate, endDate: date });
  };

  useEffect(() => {
    try {
      const touch = ('ontouchstart' in window) || (navigator.maxTouchPoints && navigator.maxTouchPoints > 0);
      setIsTouch(Boolean(touch));
    } catch (e) {
      setIsTouch(false);
    }
  }, []);

  const toInputDate = (d) => {
    if (!d) return '';
    const tzOffset = d.getTimezoneOffset() * 60000;
    return new Date(d - tzOffset).toISOString().slice(0, 10);
  };

  const fromInputDate = (value) => {
    if (!value) return null;
    const parts = value.split('-');
    if (parts.length !== 3) return null;
    const [y, m, day] = parts.map(Number);
    return new Date(y, m - 1, day);
  };

  const handleNativeStart = (e) => {
    const date = fromInputDate(e.target.value);
    if (!date) return;
    // keep endDate not earlier than start
    let newEnd = endDate;
    if (newEnd && newEnd < date) newEnd = date;
    setStartDate(date);
    setEndDate(newEnd);
    setPeriod('custom');
    onChange({ period: 'custom', startDate: date, endDate: newEnd });
  };

  const handleNativeEnd = (e) => {
    const date = fromInputDate(e.target.value);
    if (!date) return;
    let newStart = startDate;
    if (newStart && newStart > date) newStart = date;
    setEndDate(date);
    setStartDate(newStart);
    setPeriod('custom');
    onChange({ period: 'custom', startDate: newStart, endDate: date });
  };

  const handleToday = () => {
    const now = new Date();
    setStartDate(now);
    setEndDate(now);
    setPeriod('day');
    onChange({ period: 'day', startDate: now, endDate: now });
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
      <div className="flex items-center gap-2 bg-zinc-800 p-1 rounded-lg">
        {['day', 'week', 'month', 'limitless'].map((p) => (
          <button

            key={p}
            onClick={() => handlePeriodChange(p)}
            aria-pressed={period === p}
            className={`px-4 py-[6px] text-sm md:text-base font-semibold rounded-md transition-colors capitalize focus:outline-none ${period === p ? 'bg-blue-600 text-white' : 'text-zinc-300 hover:bg-zinc-700'}`}
          >
            {p}
          </button>
        ))}
        <button
          onClick={handleToday}
          className="ml-2 px-3 py-[6px] text-sm md:text-base text-zinc-200 bg-zinc-700 rounded-md hover:bg-zinc-600"
          aria-label="Set to today"
        >
          Today
        </button>
      </div>

      <div className="flex items-center gap-2">
        {isTouch ? (
          <>
            <input
              type="date"
              value={toInputDate(startDate)}
              onChange={handleNativeStart}
              className="bg-zinc-700 text-white p-3 rounded-md w-30 text-center appearance-none"
              aria-label="Start date"
            />
            <span className="text-zinc-400 px-1">to</span>
            <input
              type="date"
              value={toInputDate(endDate)}
              onChange={handleNativeEnd}
              min={toInputDate(startDate)}
              className="bg-zinc-700 text-white p-3 rounded-md w-30 text-center appearance-none"
              aria-label="End date"
            />
          </>
        ) 
        : (
          <>
            <DatePicker
              selected={startDate}
              onChange={handleStartDateChange}
              selectsStart
              startDate={startDate}
              endDate={endDate}
              className="bg-zinc-700 text-white p-2 rounded-md w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-zinc-400 px-1">to</span>
            <DatePicker
              selected={endDate}
              onChange={handleEndDateChange}
              selectsEnd
              startDate={startDate}
              endDate={endDate}
              minDate={startDate}
              className="bg-zinc-700 text-white p-2 rounded-md w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </>
        )}
      </div>
    </div>
  );
};

export default DateRangePicker;
