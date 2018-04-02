#include <Python.h>
#include <arrayobject.h>

#if _WIN32 || _WIN64
#if _WIN64
#define ENVIRONMENT64
#else
#define ENVIRONMENT32
#endif
#endif

#if __GNUC__
#if __x86_64__ || __ppc64__
#define ENVIRONMENT64
#else
#define ENVIRONMENT32
#endif
#endif

static PyObject *
iir_apply(PyObject *self, PyObject *args)
{
	// Load input arrays
    PyObject *ObjTrace,*ObjXC,*ObjYC;
    if (!PyArg_ParseTuple(args, "OOO", &ObjTrace,&ObjXC,&ObjYC))
        return NULL;
	PyArrayObject *ArrTrace=(PyArrayObject *)PyArray_FROM_OTF(ObjTrace,NPY_DOUBLE,NPY_CARRAY|NPY_ENSURECOPY);// Copy, since it's going to be an output array
	if (ArrTrace==NULL)
		return NULL;
	PyArrayObject *ArrXC=(PyArrayObject *)PyArray_FROM_OTF(ObjXC,NPY_DOUBLE,NPY_CARRAY);
	if (ArrXC==NULL)
	{
		Py_DECREF(ArrTrace);
		return NULL;
	}
	PyArrayObject *ArrYC=(PyArrayObject *)PyArray_FROM_OTF(ObjYC,NPY_DOUBLE,NPY_CARRAY);
	if (ArrYC==NULL)
	{
		Py_DECREF(ArrTrace);
		Py_DECREF(ArrXC);
		return NULL;
	}

	// Ensure required properties
	if ( ArrTrace->nd!=1 || ArrXC->nd!=1 || ArrYC->nd!=1 )
	{
		PyErr_SetString(PyExc_ValueError,"only 1D arrays are allowed");
		Py_DECREF(ArrTrace);
		Py_DECREF(ArrXC);
		Py_DECREF(ArrYC);
		return NULL;
	};
	npy_intp TraceLength=ArrTrace->dimensions[0], XCLength=ArrXC->dimensions[0], YCLength=ArrYC->dimensions[0];
	if ( XCLength==0 || XCLength>=TraceLength || YCLength>=TraceLength ) //Convolution is impossible, keep array unchanged
	{
		Py_DECREF(ArrXC);
		Py_DECREF(ArrYC);
		return (PyObject *)ArrTrace;
	};

	// Perform pass
	npy_double *TraceData=(npy_double*)ArrTrace->data, *XCData=(npy_double*)ArrXC->data, *YCData=(npy_double*)ArrYC->data;
	npy_intp i,j;
	if (XCLength-1>YCLength)
		i=XCLength-1;
	else
		i=YCLength;
	npy_double *PrevX=(npy_double *) malloc(sizeof(npy_double)*XCLength); //Ring buffer for previous x values (previous y values are taken from the array); note that time direction is opposite here
	if (PrevX==NULL)
	{
		PyErr_SetString(PyExc_MemoryError,"");
		Py_DECREF(ArrTrace);
		Py_DECREF(ArrXC);
		Py_DECREF(ArrYC);
		return NULL;
	}
	unsigned int PrevXPos=0;
	for (j=1;j<XCLength;j++)
		PrevX[j]=TraceData[i-j];
	for (;i<TraceLength;++i)
	{
		PrevX[PrevXPos]=TraceData[i];
		TraceData[i]=0;
		for (j=0;j<XCLength;j++)
			TraceData[i]+=PrevX[(PrevXPos+j)%XCLength]*XCData[j];
		for (j=0;j<YCLength;j++)
			TraceData[i]+=TraceData[i-j-1]*YCData[j];
		PrevXPos=((PrevXPos+XCLength)-1)%XCLength;
	}
	Py_DECREF(ArrXC);
	Py_DECREF(ArrYC);
	free(PrevX);
    return (PyObject *)ArrTrace;
};
char iir_apply__doc[]="iir_apply(trace, xcoeff, ycoeff)\n\n\
	Apply digital, (possibly) recursive filter with coefficients `xcoeff` and `ycoeff`.\n\n\
	Result is filtered signal `y` with ``y[n]=sum_j x[n-j]*xcoeff[j] + sum_k y[n-k-1]*ycoeff[k]`` .\n\
	All input arrays should be one-dimensional and real.";

static PyMethodDef ExtMethods[] = 
{
	{"iir_apply",iir_apply,METH_VARARGS,iir_apply__doc},
	{NULL, NULL, 0, NULL}
};



#ifdef ENVIRONMENT32
static struct PyModuleDef iir_transform_module = {
    PyModuleDef_HEAD_INIT,
    "iir_transform_py36_32",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
	ExtMethods
};
PyMODINIT_FUNC
PyInit_iir_transform_py36_32()
{
	PyObject *module=PyModule_Create(&iir_transform_module);
	import_array();
	return module;
};
#endif

#ifdef ENVIRONMENT64
static struct PyModuleDef iir_transform_module = {
    PyModuleDef_HEAD_INIT,
    "iir_transform_py36_64",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
	ExtMethods
};
PyMODINIT_FUNC
PyInit_iir_transform_py36_64()
{
	PyObject *module=PyModule_Create(&iir_transform_module);
	import_array();
	return module;
};
#endif