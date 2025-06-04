import { configureStore } from '@reduxjs/toolkit';
import batchReducer from './batchSlice';
import historyPanelReducer from './historyPanelSlice';
import modernizationReducer from './modernizationSlice';
import fileReducer from './uploadFileSlice';

export const store = configureStore({
    reducer: {
        batch: batchReducer,
        fileUpload: fileReducer,
        historyPanel: historyPanelReducer,
        modernizationReducer: modernizationReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
